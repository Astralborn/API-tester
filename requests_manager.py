import os
import json
import re

import requests
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from constants import JSON_FOLDER, LOGS_FOLDER

os.makedirs(LOGS_FOLDER, exist_ok=True)

def make_safe_filename(name: str) -> str:
    # replace anything that is not alphanumeric, dot, or underscore with underscore
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)
# -------------------- Worker Thread --------------------

class RequestWorker(QThread):
    finished = Signal(str, str, str)  # text, preset_name, tag

    def __init__(self, url, user, password, payload, preset_name="", json_type="normal", log_file=None):
        super().__init__()
        self.url = url
        self.user = user
        self.password = password
        self.payload = payload
        self.preset_name = preset_name
        self.json_type = json_type
        self.log_file = log_file  # optional: shared log file

    def run(self):
        # -------------------- Ensure log file exists --------------------
        if not self.log_file:
            safe_name = make_safe_filename(self.preset_name or "request")
            self.log_file = os.path.join(
                LOGS_FOLDER,
                f"log_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )

        try:
            response = requests.post(
                self.url,
                json=self.payload,
                auth=requests.auth.HTTPDigestAuth(self.user, self.password),
                headers={"Content-Type": "application/json"},
                timeout=10,
                verify=False
            )

            text = f"URL: {self.url}\nPayload: {json.dumps(self.payload, indent=2)}\n" \
                   f"Status Code: {response.status_code}\n{response.text}"

            tag = "ok" if response.status_code == 200 else "warn"

        except requests.exceptions.RequestException as e:
            text = f"Request Error: {e}"
            tag = "err"

        # -------------------- Log to file --------------------
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                # Add preset header if not single request
                if "MultiPreset_Run" in self.log_file:
                    f.write(f"\n--- Preset: {self.preset_name} ---\n")
                f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(f"Tag: {tag}\n")
                f.write(f"{text}\n")
        except Exception as log_err:
            print(f"Logging error: {log_err}")

        # -------------------- Emit result to GUI --------------------
        self.finished.emit(text, self.preset_name, tag)


# -------------------- Request Manager --------------------
class RequestManager:
    def __init__(self):
        self.workers = []
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

    def build_request(self, ip, endpoint, json_file, simple_format=False):
        url = f"http://{ip}{endpoint}"
        if simple_format:
            url += "&format=simple" if "?" in url else "?format=simple"

        payload = {}
        if json_file and json_file != "(none)":
            try:
                json_file_clean = json_file.strip().replace("\\", "/")
                full_path = os.path.join(JSON_FOLDER, *json_file_clean.split("/"))
                with open(full_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception as e:
                print(f"Failed to load JSON file '{json_file}': {e}")
                payload = {}

        return url, payload

    def start_new_log(self, preset_name):
        safe_name = make_safe_filename(preset_name or "request")
        log_file = os.path.join(
            LOGS_FOLDER,
            f"log_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        return log_file

    def send_request_async(
        self, ip, user, password, endpoint, json_file, simple_format, json_type, callback, preset_name="", log_file=None
    ):
        url, payload = self.build_request(ip, endpoint, json_file, simple_format)

        worker = RequestWorker(
            url=url,
            user=user,
            password=password,
            payload=payload,
            preset_name=preset_name,
            json_type=json_type,
            log_file=log_file
        )

        worker.finished.connect(callback)
        self.workers.append(worker)
        worker.start()
