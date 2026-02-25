"""App package for API Test Tool."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from constants import resource_path
from di_container import DIContainer, PresetManagerProtocol, RequestManagerProtocol, SettingsManagerProtocol
from logging_system import get_logger

# Import mixins
from app.ui_builder import UIBuilderMixin
from app.request_handling import RequestHandlingMixin
from app.settings_handling import SettingsHandlingMixin
from app.preset_handling import PresetHandlingMixin

if TYPE_CHECKING:
    from requests_manager import RequestWorker


class ApiTestApp(
    QWidget,
    UIBuilderMixin,
    RequestHandlingMixin,
    SettingsHandlingMixin,
    PresetHandlingMixin
):
    """Main API Test application widget."""

    def __init__(
        self,
        preset_manager: PresetManagerProtocol | None = None,
        request_manager: RequestManagerProtocol | None = None,
        settings_manager: SettingsManagerProtocol | None = None,
        container: DIContainer | None = None,
    ) -> None:
        super().__init__()

        # Use dependency injection or create defaults
        if container:
            self.container = container
            self.presets = preset_manager or container.get("preset_manager")
            self.requests = request_manager or container.get("request_manager")
            self.settings = settings_manager or container.get("settings_manager")
        else:
            # Fallback to direct instantiation for backward compatibility
            from presets import PresetManager
            from requests_manager import RequestManager
            from settings import SettingsManager

            self.presets = preset_manager or PresetManager()
            self.requests = request_manager or RequestManager()
            self.settings = settings_manager or SettingsManager()
            self.container = None

        # Initialize logging
        self.logger = get_logger("api_test_app")
        self.logger.log_application_event(
            "application_started",
            window_geometry="1200x720",
            python_version=sys.version,
        )

        self.setWindowTitle("API Test Tool")
        # QIcon requires str — resource_path now returns Path so we convert
        self.setWindowIcon(QIcon(str(resource_path("api_tester_icon.ico"))))
        self.resize(1200, 720)

        # Request tracking
        self.active_requests: list[RequestWorker] = []
        self.current_request_count = 0
        self.total_request_count = 0

        # UI elements (initialized by UI builder mixin)
        self.preset_combo = None
        self.preset_search = None
        self.test_mode_combo = None
        self.endpoint_combo = None
        self.json_combo = None
        self.json_type_combo = None
        self.ip_edit = None
        self.user_edit = None
        self.pass_edit = None
        self.simple_check = None
        self.response = None
        self.status = None
        self.btn_send = None
        self.btn_multi = None
        self.btn_clear = None
        self.btn_cancel = None

        # Theme + UI
        self.apply_light_theme()
        self.build_ui()
        self.load_settings()
        self.update_presets_list()

        # Connect window geometry auto-save
        self._setup_geometry_auto_save()

    def close_event(self, event) -> None:
        """Handle application close event - save settings."""
        self.save_settings()
        # Cancel any active requests
        if self.active_requests:
            self.cancel_all_requests()
        super().close_event(event)