"""Request handling module for API Test Tool."""
from __future__ import annotations

import json
import ipaddress
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QTextCursor

if TYPE_CHECKING:
    from requests_manager import RequestWorker


class RequestHandlingMixin:
    """Mixin providing request handling functionality."""

    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def send_request(self) -> None:
        """Send a single API request."""
        ip = self.ip_edit.text().strip()
        if not ip:
            self.logger.log_user_action("send_request_failed", reason="no_ip")
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        # Validate IP format
        if not self._validate_ip(ip):
            self.logger.log_user_action("send_request_failed", reason="invalid_ip", ip=ip)
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return

        # Check if username is provided for authentication
        if not self.user_edit.text().strip():
            self.logger.log_user_action("send_request_failed", reason="no_username")
            QMessageBox.warning(self, "Error", "Username required for authentication")
            return

        # Log request start
        endpoint = self.endpoint_combo.currentText()
        self.logger.log_user_action("send_request_started", 
                                   ip=ip, 
                                   endpoint=endpoint,
                                   json_file=self.json_combo.currentText())

        self.status.setText("Sending request...")

        def on_response(text: str, preset_name: str, tag: str) -> None:
            self.display_response(text, preset_name, tag)
            self.status.setText("Request finished successfully")
            self.logger.log_request("POST", f"http://{ip}{endpoint}", 
                                   200 if tag == "ok" else 400, 0.0,
                                   preset_name=preset_name, response_tag=tag)

        try:
            worker = self.requests.send_request_async(
                ip,
                self.user_edit.text(),
                self.pass_edit.text(),
                endpoint,
                self.json_combo.currentText(),
                self.simple_check.isChecked(),
                self.json_type_combo.currentText(),
                on_response,
                preset_name=self.endpoint_combo.currentText(),
            )
            
            # Track the request for cancellation
            self._track_request(worker)
            
            # Handle request completion
            def on_finished():
                self._untrack_request(worker)
            
            worker.finished.connect(on_finished)
            
        except Exception as e:
            self.logger.exception("Failed to send request", ip=ip, endpoint=endpoint)
            QMessageBox.critical(self, "Error", f"Failed to send request: {str(e)}")
            self.status.setText("Request failed")

    def cancel_all_requests(self) -> None:
        """Cancel all active requests."""
        if not self.active_requests:
            return
        
        for worker in self.active_requests:
            worker.terminate()
            worker.wait()  # Wait for thread to finish
        
        self.active_requests.clear()
        self.current_request_count = 0
        self.total_request_count = 0
        
        self.btn_cancel.setEnabled(False)
        self.status.setText("All requests cancelled")

    def _track_request(self, worker: RequestWorker) -> None:
        """Track a new request worker."""
        self.active_requests.append(worker)
        self.current_request_count += 1
        
        # Enable cancel button when there are active requests
        if len(self.active_requests) == 1:
            self.btn_cancel.setEnabled(True)

    def _untrack_request(self, worker: RequestWorker) -> None:
        """Remove completed request worker from tracking."""
        if worker in self.active_requests:
            self.active_requests.remove(worker)
        
        # Disable cancel button when no active requests
        if not self.active_requests:
            self.btn_cancel.setEnabled(False)
            self.current_request_count = 0
            self.total_request_count = 0

    def _update_progress(self, completed: int, total: int) -> None:
        """Update progress display."""
        if total > 1:  # Only show progress for multiple requests
            self.status.setText(f"Progress: {completed}/{total} requests")

    def _format_json_response(self, text: str) -> str:
        """Try to extract and format JSON from response text."""
        try:
            if "{" in text:
                idx = text.index("{")
                obj = json.loads(text[idx:])
                formatted_json = json.dumps(obj, indent=2, ensure_ascii=False)
                return text[:idx] + formatted_json
        except Exception:
            pass
        return text

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _build_response_html(self, text: str, preset_name: str, tag: str) -> str:
        """Build HTML for response display."""
        separator = '<div style="border-top: 1px solid #c0c0c0; margin: 4px 0;"></div>'
        header_style = 'font-weight: 600; color: #666666; margin-bottom: 8px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;'
        body_style = 'font-family: Consolas, monospace; font-size: 12px; line-height: 1.5; color: #333333;'
        
        header = f'<div style="{header_style}">{preset_name or "Request"}</div><br>'
        body = self._escape_html(text).replace("\n", "<br>")
        
        return f'{separator}<div style="{body_style}">{header}{body}</div>'

    def display_response(self, text: str, preset_name: str, tag: str) -> None:
        """Display formatted response in the response area."""
        formatted_text = self._format_json_response(text)
        html = self._build_response_html(formatted_text, preset_name, tag)
        
        self.response.moveCursor(QTextCursor.End)
        self.response.insertHtml(html)
        self.response.moveCursor(QTextCursor.End)

    def clear_response(self) -> None:
        """Clear the response display area."""
        self.response.clear()
