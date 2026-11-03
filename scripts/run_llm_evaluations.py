import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from source.services.llm_evaluation import evaluate_suite  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TruthFit analysis output against fixtures.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT_DIR / "evaluations" / "v1" / "cases.json",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT_DIR / "evaluations" / "v1" / "baseline-results.json",
    )
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    report = evaluate_suite(cases, results)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
