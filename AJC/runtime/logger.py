import logging
from datetime import datetime
from pathlib import Path
import json
import threading

from .paths import LOGS_DIR

MAX_LOG_FILES = 5


def _prune_logs(log_dir: Path, pattern: str) -> None:
    files = sorted(log_dir.glob(pattern))
    if len(files) <= MAX_LOG_FILES:
        return
    for old in files[:-MAX_LOG_FILES]:
        try:
            old.unlink()
        except OSError:
            pass


def setup_logger():
    """Configure logger for Anki Jisho Connect."""
    logger = logging.getLogger("ajc_jisho_connect")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    log_dir = LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    _prune_logs(log_dir, "jisho_connect_*.log")
    _prune_logs(log_dir, "jisho_connect_errors_*.log")

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"jisho_connect_{date_str}.log"
    error_file = log_dir / f"jisho_connect_errors_{date_str}.log"

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)

    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
    handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(error_handler)

    # Structured debug log (JSONL), pruned to the last 5 files (same policy as .log files).
    _prune_logs(log_dir, "jisho_connect_events_*.jsonl")
    events_file = log_dir / f"jisho_connect_events_{date_str}.jsonl"
    try:
        events_file.touch(exist_ok=True)
    except OSError:
        pass


    class JsonlEventHandler(logging.Handler):
        def __init__(self, path: Path):
            super().__init__()
            self.path = path
            self._lock = threading.Lock()

        def emit(self, record: logging.LogRecord) -> None:
            try:
                details = {}
                if hasattr(record, "extra"):
                    details["extra"] = record.extra
                if hasattr(record, "traceback"):
                    details["traceback"] = record.traceback
                if record.exc_info:
                    import traceback as _tb
                    details["exception"] = "".join(_tb.format_exception(*record.exc_info))

                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event": record.getMessage(),
                    "category": record.levelname.lower(),
                    "context": {
                        "logger": record.name,
                        "module": record.module,
                        "func": record.funcName,
                        "line": record.lineno,
                    },
                    "details": details,
                }
                with self._lock:
                    with self.path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                # Never let logging break the add-on.
                pass

    json_handler = JsonlEventHandler(events_file)
    json_handler.setLevel(logging.DEBUG)
    logger.addHandler(json_handler)


    return logger


logger = setup_logger()
