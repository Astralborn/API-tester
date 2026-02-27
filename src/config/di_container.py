from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


# ================= Protocols =================

@runtime_checkable
class PresetManagerProtocol(Protocol):
    def load_presets(self) -> list[dict[str, Any]]: ...
    def save_presets(self, presets: list[dict[str, Any]]) -> None: ...
    def add_preset(self, preset: dict[str, Any]) -> None: ...
    def get_by_name(self, name: str) -> dict[str, Any] | None: ...
    def delete_preset(self, name: str) -> bool: ...


@runtime_checkable
class RequestManagerProtocol(Protocol):
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
    ) -> Any: ...

    def build_request(
        self, ip: str, endpoint: str, json_file: str, simple_format: bool
    ) -> tuple[str, str]: ...


@runtime_checkable
class SettingsManagerProtocol(Protocol):
    def load_settings(self) -> None: ...
    def save_settings(self) -> None: ...
    def get_last_ip(self) -> str: ...
    def set_last_ip(self, ip: str) -> None: ...
    def get_last_user(self) -> str: ...
    def set_last_user(self, user: str) -> None: ...
    def get_window_geometry(self) -> str: ...
    def set_window_geometry(self, geometry: str) -> None: ...


# ================= DI Container =================

class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[str, dict[str, Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register(self, name: str, factory: Callable[[], Any], singleton: bool = False) -> None:
        self._services[name] = {"factory": factory, "singleton": singleton}

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        service = self._services[name]
        if service["singleton"]:
            if name not in self._singletons:
                self._singletons[name] = service["factory"]()
            return self._singletons[name]
        return service["factory"]()

    def register_defaults(self) -> None:
        from managers.presets import PresetManager
        from managers.requests_manager import RequestManager
        from managers.settings import SettingsManager

        self.register("preset_manager",  lambda: PresetManager(),  singleton=True)
        self.register("request_manager", lambda: RequestManager(), singleton=True)
        self.register("settings_manager",lambda: SettingsManager(),singleton=True)


_container = DIContainer()
_container.register_defaults()


def get_container() -> DIContainer:
    return _container


def resolve(service_name: str) -> Any:
    return _container.get(service_name)
