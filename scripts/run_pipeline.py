"""CLI entry point to run the full analytics pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from main import run_full_pipeline  # noqa: E402

if __name__ == "__main__":
    run_full_pipeline(send_email=True)
