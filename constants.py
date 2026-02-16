import sys
from pathlib import Path
from typing import Final


# ================= Resource Paths =================

def resource_path(relative_path: str) -> str:
    """
    Return absolute path to a resource (JSON, presets, logs).
    Works for both Python scripts and PyInstaller EXE (--onedir).
    """
    base_dir = (
        Path(sys.executable).parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    return str(base_dir / relative_path)


# ================= Folders & Files =================

JSON_FOLDER: Final[str] = resource_path("json_configs")
LOGS_FOLDER: Final[str] = resource_path("logs")
PRESETS_FILE: Final[str] = resource_path("presets.json")


# ================= Theme Colors =================

class LightTheme:
    BG: Final[str] = "#f0f0f0"
    ENTRY_BG: Final[str] = "#ffffff"
    TEXT_COLOR: Final[str] = "#000000"
    BTN_ACTIVE: Final[str] = "#d0d0d0"
    STATUS_BG: Final[str] = "#e0e0e0"

    RESP_OK: Final[str] = "#e0ffe0"
    RESP_WARN: Final[str] = "#fff4e0"
    RESP_ERR: Final[str] = "#ffe0e0"


# ================= API Modes =================

JSON_TYPES: Final[list[str]] = [
    "Normal JSON",
    "Google JSON",
    "JSON-RPC",
]

METHOD_IN_OPTIONS: Final[list[str]] = [
    "Method in Path",
    "Method in Action",
    "Method in JSON Body",
]


# ================= VAPIX Endpoints =================

VAPIX_ENDPOINTS: Final[list[str]] = [
    # -------- Base --------
    "/vapix/call",
    "/vapix/intercom/",

    # -------- Contacts / Intercom --------
    "/vapix/intercom/GetContacts",
    "/vapix/intercom/SetContacts",
    "/vapix/intercom/RemoveContacts",

    # -------- SIP Accounts --------
    "/vapix/call/GetSIPAccount",
    "/vapix/call/GetSIPAccounts",
    "/vapix/call/SetSIPAccount",
    "/vapix/call/SetSIPAccounts",
    "/vapix/call/RemoveSIPAccount",
    "/vapix/call/RemoveSIPAccounts",
    "/vapix/call/GetSIPAccountStatus",

    # -------- Service / Capabilities --------
    "/vapix/call/GetServiceCapabilities",
    "/vapix/call/GetSupportedSIPAccountAttributes",
    "/vapix/call/GetSupportedSIPConfigurationAttributes",
    "/vapix/call/GetSIPConfiguration",
    "/vapix/call/SetSIPConfiguration",
    "/vapix/call/GetSupportedMediaEncryptionModes",

    # -------- Audio / Codecs --------
    "/vapix/call/GetDefaultAudioCodecs",
    "/vapix/call/GetSupportedAudioCodecs",
    "/vapix/call/GetAudioCodecs",
    "/vapix/call/SetAudioCodecs",

    # -------- Call Control --------
    "/vapix/call/Call",
    "/vapix/call/GetCallStatus",
    "/vapix/call/TerminateCall",
]
