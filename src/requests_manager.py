from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests
from PySide6.QtCore import QThread, Signal

from constants import JSON_FOLDER, LOGS_FOLDER


# Ensure logs directory exists
Path(LOGS_FOLDER).mkdir(parents=True, exist_ok=True)


# ================= Helpers =================

def make_safe_filename(name: str) -> str:
    """Replace unsafe filename characters with underscore."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ================= Worker Thread =================

class RequestWorker(QThread):
    finished = Signal(str, str, str)  # text, preset_name, tag

    def __init__(
        self,
        url: str,
        user: str,
        password: str,
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

    # ---------- Main thread execution ----------

    def run(self) -> None:
        """Execute HTTP request and emit result."""
        self._ensure_log_file()

        try:
            response = requests.post(
                self.url,
                json=self.payload,
                auth=requests.auth.HTTPDigestAuth(self.user, self.password),
                headers={"Content-Type": "application/json"},
                timeout=10,
                verify=False,
            )

            text = (
                f"URL: {self.url}\n"
                f"Payload: {json.dumps(self.payload, indent=2, ensure_ascii=False)}\n"
                f"Status Code: {response.status_code}\n"
                f"{response.text}"
            )

            tag = "ok" if response.status_code == 200 else "warn"

        except requests.exceptions.RequestException as exc:
            text = f"Request Error: {exc}"
            tag = "err"

        self._write_log(text, tag)
        self.finished.emit(text, self.preset_name, tag)

    # ---------- Internal helpers ----------

    def _ensure_log_file(self) -> None:
        """Create log file path if not provided."""
        if self.log_file:
            return

        safe_name = make_safe_filename(self.preset_name or "request")
        self.log_file = Path(LOGS_FOLDER) / f"log_{safe_name}_{_timestamp()}.log"

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
            print(f"Logging error: {exc}")


# ================= Request Manager =================

class RequestManager:
    def __init__(self) -> None:
        self.workers: list[RequestWorker] = []

        # Disable SSL warnings (intentional for device APIs)
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
                json_path = Path(JSON_FOLDER) / Path(json_file.strip())
                with json_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception as exc:
                print(f"Failed to load JSON file '{json_file}': {exc}")

        return url, payload

    # ---------- Logging ----------

    def start_new_log(self, preset_name: str) -> Path:
        """Create new log file path."""
        safe_name = make_safe_filename(preset_name or "request")
        return Path(LOGS_FOLDER) / f"log_{safe_name}_{_timestamp()}.log"

    # ---------- Async request ----------

    def send_request_async(
        self,
        ip: str,
        user: str,
        password: str,
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
        self.workers.append(worker)
        worker.start()
        
        return worker
