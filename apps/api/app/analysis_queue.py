from fastapi import BackgroundTasks

from apps.api.app.config import analysis_queue_backend, redis_url


def enqueue_analysis(
    background_tasks: BackgroundTasks,
    run_id: str,
    payload: dict,
    request_id: str,
) -> None:
    if analysis_queue_backend() == "rq":
        from redis import Redis
        from rq import Queue

        safe_payload = dict(payload)
        safe_payload["api_key"] = ""
        queue = Queue("truthfit-analysis", connection=Redis.from_url(redis_url()))
        queue.enqueue(
            "apps.api.app.tasks.process_analysis_task",
            run_id,
            safe_payload,
            request_id,
            job_timeout=240,
            result_ttl=3600,
        )
        return

    background_tasks.add_task(process_analysis_locally, run_id, payload, request_id)


def process_analysis_locally(run_id: str, payload: dict, request_id: str) -> None:
    from apps.api.app.tasks import process_analysis_task

    process_analysis_task(run_id, payload, request_id)
