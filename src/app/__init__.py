"""App package for API Test Tool."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from config.constants import resource_path
from config.di_container import DIContainer, PresetManagerProtocol, RequestManagerProtocol, SettingsManagerProtocol
from config.logging_system import get_logger

from app.ui_builder import UIBuilderMixin
from app.request_handling import RequestHandlingMixin
from app.settings_handling import SettingsHandlingMixin
from app.preset_handling import PresetHandlingMixin

if TYPE_CHECKING:
    from managers.requests_manager import RequestWorker


class ApiTestApp(
    QWidget,
    UIBuilderMixin,
    RequestHandlingMixin,
    SettingsHandlingMixin,
    PresetHandlingMixin,
):
    """Main API Test application widget — assembled via mixin composition."""

    def __init__(
        self,
        preset_manager: PresetManagerProtocol | None = None,
        request_manager: RequestManagerProtocol | None = None,
        settings_manager: SettingsManagerProtocol | None = None,
        container: DIContainer | None = None,
    ) -> None:
        super().__init__()

        if container:
            self.container = container
            self.presets  = preset_manager  or container.get("preset_manager")
            self.requests = request_manager or container.get("request_manager")
            self.settings = settings_manager or container.get("settings_manager")
        else:
            from managers.presets import PresetManager
            from managers.requests_manager import RequestManager
            from managers.settings import SettingsManager
            self.presets  = preset_manager  or PresetManager()
            self.requests = request_manager or RequestManager()
            self.settings = settings_manager or SettingsManager()
            self.container = None

        self.logger = get_logger("api_test_app")
        self.logger.log_application_event(
            "application_started",
            window_geometry="1200x720",
            python_version=sys.version,
        )

        self.setWindowTitle("API Test Tool")
        self.setWindowIcon(QIcon(str(resource_path("api_tester_icon.ico"))))
        self.resize(1200, 720)

        # Request tracking
        self.active_requests: list[RequestWorker] = []
        self.current_request_count: int = 0
        self.total_request_count: int = 0

        self.apply_light_theme()
        self.build_ui()
        self.load_settings()
        self.update_presets_list()
        self._setup_geometry_auto_save()

    def closeEvent(self, event) -> None:
        self.save_settings()
        if self.active_requests:
            self.cancel_all_requests()
        super().closeEvent(event)
