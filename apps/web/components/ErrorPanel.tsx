export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="alert">
      <strong>Could not load this view.</strong>
      <p>{message}</p>
      <p className="muted">
        Start the local analysis service with: .\.codex-run-venv\Scripts\python.exe -m uvicorn
        apps.api.app.main:app --reload --env-file .env
      </p>
    </div>
  );
}
