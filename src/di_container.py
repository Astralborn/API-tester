from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


# ================= Protocols for Dependency Injection =================

@runtime_checkable
class PresetManagerProtocol(Protocol):
    """Protocol for preset manager dependency injection."""

    def load_presets(self) -> list[dict[str, Any]]:
        """Load all presets."""
        ...

    def save_presets(self, presets: list[dict[str, Any]]) -> None:
        """Save presets to file."""
        ...

    def add_preset(self, preset: dict[str, Any]) -> None:
        """Add a new preset."""
        ...

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Get preset by name."""
        ...

    def delete_preset(self, name: str) -> bool:
        """Delete preset by name."""
        ...


@runtime_checkable
class RequestManagerProtocol(Protocol):
    """Protocol for request manager dependency injection."""

    def send_request_async(
        self,
        ip: str,
        user: str,
        password: bytearray,
        endpoint: str,
        json_file: str,
        simple_format: bool,
        json_type: str,
        callback: Callable[..., Any],
        preset_name: str = "",
    ) -> Any:
        """Send async request and return worker."""
        ...

    def build_request(
        self, ip: str, endpoint: str, json_file: str, simple_format: bool
    ) -> tuple[str, str]:
        """Build request URL and payload."""
        ...


@runtime_checkable
class SettingsManagerProtocol(Protocol):
    """Protocol for settings manager dependency injection."""

    def load_settings(self) -> None:
        """Load settings from file."""
        ...

    def save_settings(self) -> None:
        """Save settings to file."""
        ...

    def get_last_ip(self) -> str:
        """Get last used IP."""
        ...

    def set_last_ip(self, ip: str) -> None:
        """Set last used IP."""
        ...

    def get_last_user(self) -> str:
        """Get last used username."""
        ...

    def set_last_user(self, user: str) -> None:
        """Set last used username."""
        ...

    def get_window_geometry(self) -> str:
        """Get window geometry."""
        ...

    def set_window_geometry(self, geometry: str) -> None:
        """Set window geometry."""
        ...


# ================= Dependency Container =================

class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[str, dict[str, Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register(self, name: str, factory: Callable[[], Any], singleton: bool = False) -> None:
        """Register a service with optional singleton pattern."""
        self._services[name] = {"factory": factory, "singleton": singleton}

    def get(self, name: str) -> Any:
        """Get a service instance."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")

        service = self._services[name]

        if service["singleton"]:
            if name not in self._singletons:
                self._singletons[name] = service["factory"]()
            return self._singletons[name]
        else:
            return service["factory"]()

    def register_defaults(self) -> None:
        """Register default implementations."""
        from presets import PresetManager
        from requests_manager import RequestManager
        from settings import SettingsManager

        self.register("preset_manager", lambda: PresetManager(), singleton=True)
        self.register("request_manager", lambda: RequestManager(), singleton=True)
        self.register("settings_manager", lambda: SettingsManager(), singleton=True)


# Global container instance
_container = DIContainer()
_container.register_defaults()


def get_container() -> DIContainer:
    """Get the global dependency container."""
    return _container


def resolve(service_name: str) -> Any:
    """Resolve a service from the container."""
    return _container.get(service_name)