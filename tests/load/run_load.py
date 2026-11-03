import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from statistics import median
from time import perf_counter
from uuid import uuid4

import httpx


def _request(base_url: str, token: str, scenario: str, index: int) -> tuple[int, float]:
    headers = {"authorization": f"Bearer {token}"}
    started = perf_counter()
    with httpx.Client(base_url=base_url, timeout=30) as client:
        if scenario == "parse":
            response = client.post(
                "/resumes/parse",
                headers=headers,
                files={"file": ("resume.txt", b"Python SQL ETL PostgreSQL", "text/plain")},
            )
        else:
            response = client.post(
                "/analysis/run",
                headers={**headers, "idempotency-key": f"load-{index}-{uuid4().hex}"},
                json={
                    "resume_text": "Python SQL ETL PostgreSQL",
                    "job_description": "Data Engineer requiring Python, SQL, and ETL",
                    "provider": "Gemini",
                    "model": "gemini-3.8-flash",
                },
            )
    return response.status_code, perf_counter() - started


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def run(base_url: str, token: str, scenario: str, requests: int, concurrency: int) -> dict:
    started = perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(_request, base_url, token, scenario, index)
            for index in range(requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    elapsed = perf_counter() - started
    durations = [duration for _, duration in results]
    expected_status = 200 if scenario == "parse" else 202
    failures = sum(status != expected_status for status, _ in results)
    return {
        "scenario": scenario,
        "requests": requests,
        "concurrency": concurrency,
        "failures": failures,
        "requests_per_second": round(requests / elapsed, 2),
        "median_ms": round(median(durations) * 1000, 1),
        "p95_ms": round(_percentile(durations, 0.95) * 1000, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded TruthFit API load scenarios.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--token", required=True)
    parser.add_argument("--scenario", choices=["parse", "analysis"], required=True)
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.concurrency > args.requests:
        raise SystemExit("Use positive counts with concurrency no greater than requests.")

    result = run(args.base_url, args.token, args.scenario, args.requests, args.concurrency)
    print(json.dumps(result, indent=2))
    if result["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
