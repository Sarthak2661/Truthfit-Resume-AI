import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from source.ai.schemas import analysis_json_schema  # noqa: E402


def main() -> None:
    output_path = ROOT_DIR / "docs" / "analysis-result.schema.json"
    output_path.write_text(
        json.dumps(analysis_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
