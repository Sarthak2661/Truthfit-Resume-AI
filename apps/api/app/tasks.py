from apps.api.app.services.analysis_service import process_analysis_run


def process_analysis_task(run_id: str, payload: dict, request_id: str) -> None:
    process_analysis_run(run_id=run_id, payload_data=payload, request_id=request_id)
