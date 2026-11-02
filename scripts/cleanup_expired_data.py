from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.services.privacy_service import cleanup_expired_data  # noqa: E402


if __name__ == "__main__":
    deleted = cleanup_expired_data()
    print(
        "Deleted "
        f"{deleted['analyses']} analyses, "
        f"{deleted['resumes']} resumes, and "
        f"{deleted['jobs']} jobs."
    )
