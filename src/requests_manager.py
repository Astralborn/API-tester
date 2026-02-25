from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests
from PySide6.QtCore import QThread, Signal

from constants import JSON_FOLDER, LOGS_FOLDER
from logging_system import get_logger


# Ensure logs directory exists
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

_logger = get_logger("request_manager")

# Maximum characters allowed in a generated filename segment.
# Most filesystems support 255 bytes; we stay well under that because
# the full log filename also includes a timestamp suffix.
_FILENAME_MAX_LEN = 64


# ================= Helpers =================

def make_safe_filename(name: str) -> str:
    """Replace unsafe filename characters with underscore, capped at 64 chars."""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return safe[:_FILENAME_MAX_LEN]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ================= Worker Thread =================

class RequestWorker(QThread):
    finished = Signal(str, str, str)  # text, preset_name, tag

    def __init__(
        self,
        url: str,
        user: str,
        # bytearray instead of str — mutable so we can zero it after use,
        # minimising the window the plaintext password lives in memory.
        password: bytearray,
        payload: dict[str, Any],
        preset_name: str = "",
        json_type: str = "normal",
        log_file: Path | None = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.user = user
        self.password = password
        self.payload = payload
        self.preset_name = preset_name
        self.json_type = json_type
        self.log_file = log_file

        self.logger = get_logger("request_worker")

    # ---------- Main thread execution ----------

    def run(self) -> None:
        """Execute HTTP request and emit result."""
        self._ensure_log_file()

        self.logger.info(
            f"Starting request to {self.url}",
            url=self.url,
            user=self.user,
            preset_name=self.preset_name,
            payload_size=len(json.dumps(self.payload)),
        )

        try:
            # Decode to str only at the point of use, then zero the bytearray
            # immediately so the plaintext doesn't linger in memory.
            password_str = self.password.decode("utf-8")
            response = requests.post(
                self.url,
                json=self.payload,
                auth=requests.auth.HTTPDigestAuth(self.user, password_str),
                headers={"Content-Type": "application/json"},
                timeout=10,
                # Target devices use self-signed certificates. SSL verification
                # is intentionally disabled for this internal QA tool.
                verify=False,
            )
            del password_str
            self.password[:] = b"\x00" * len(self.password)

            text = (
                f"URL: {self.url}\n"
                f"Payload: {json.dumps(self.payload, indent=2, ensure_ascii=False)}\n"
                f"Status Code: {response.status_code}\n"
                f"{response.text}"
            )

            tag = "ok" if response.status_code == 200 else "warn"

            self.logger.log_request(
                "POST",
                self.url,
                response.status_code,
                response.elapsed.total_seconds(),
                preset_name=self.preset_name,
                response_size=len(response.text),
            )

        except requests.exceptions.RequestException as exc:
            self.password[:] = b"\x00" * len(self.password)
            text = f"Request Error: {exc}"
            tag = "err"

            self.logger.error(
                f"Request failed: {exc}",
                url=self.url,
                user=self.user,
                preset_name=self.preset_name,
                error_type=type(exc).__name__,
            )

        self._write_log(text, tag)
        self.finished.emit(text, self.preset_name, tag)

    # ---------- Internal helpers ----------

    def _ensure_log_file(self) -> None:
        """Create log file path if not provided."""
        if self.log_file:
            return

        safe_name = make_safe_filename(self.preset_name or "request")
        self.log_file = LOGS_FOLDER / f"log_{safe_name}_{_timestamp()}.log"

    def _write_log(self, text: str, tag: str) -> None:
        """Append request result to log file."""
        if not self.log_file:
            return

        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                if "MultiPreset_Run" in self.log_file.name:
                    f.write(f"\n--- Preset: {self.preset_name} ---\n")

                f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
                f.write(f"Tag: {tag}\n{text}\n")

        except Exception as exc:
            self.logger.error(
                "Failed to write log file",
                file=str(self.log_file),
                error=str(exc),
            )


# ================= Request Manager =================

class RequestManager:
    def __init__(self) -> None:
        self.workers: list[RequestWorker] = []

        # Suppress urllib3 warnings that would otherwise fire on every request
        # because target devices use self-signed certificates (verify=False).
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

    # ---------- Build request ----------

    def build_request(
        self,
        ip: str,
        endpoint: str,
        json_file: str | None,
        simple_format: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        """Return URL and payload loaded from JSON file."""
        url = f"http://{ip}{endpoint}"

        if simple_format:
            url += "&format=simple" if "?" in url else "?format=simple"

        payload: dict[str, Any] = {}

        if json_file and json_file != "(none)":
            try:
                json_path = JSON_FOLDER / json_file.strip()
                with json_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception as exc:
                _logger.error(
                    f"Failed to load JSON file '{json_file}'",
                    file=json_file,
                    error=str(exc),
                )

        return url, payload

    # ---------- Logging ----------

    def start_new_log(self, preset_name: str) -> Path:
        """Create new log file path."""
        safe_name = make_safe_filename(preset_name or "request")
        return LOGS_FOLDER / f"log_{safe_name}_{_timestamp()}.log"

    # ---------- Worker cleanup ----------

    def _remove_worker(self, worker: RequestWorker) -> None:
        """Remove a finished worker from the tracking list."""
        try:
            self.workers.remove(worker)
        except ValueError:
            pass  # Already removed (e.g. via cancel)

    # ---------- Async request ----------

    def send_request_async(
        self,
        ip: str,
        user: str,
        password: bytearray,
        endpoint: str,
        json_file: str | None,
        simple_format: bool,
        json_type: str,
        callback: Callable[[str, str, str], None],
        preset_name: str = "",
        log_file: Path | None = None,
    ) -> RequestWorker:
        """Start background request worker and return the worker instance."""
        url, payload = self.build_request(ip, endpoint, json_file, simple_format)

        worker = RequestWorker(
            url=url,
            user=user,
            password=password,
            payload=payload,
            preset_name=preset_name,
            json_type=json_type,
            log_file=log_file,
        )

        worker.finished.connect(callback)
        # Auto-remove from list when done — prevents unbounded growth
        worker.finished.connect(lambda *_: self._remove_worker(worker))
        self.workers.append(worker)
        worker.start()

        return worker