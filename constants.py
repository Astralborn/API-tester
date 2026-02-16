import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Returns the absolute path to a resource (JSON, presets, logs),
    works for both scripts and EXE (PyInstaller --onedir).
    """
    if getattr(sys, "frozen", False):  # Running as EXE
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


# ---------------- Folders & Files ----------------
JSON_FOLDER = resource_path("json_configs")
LOGS_FOLDER = resource_path("logs")
PRESETS_FILE = resource_path("presets.json")

# Light Theme Colors
LIGHT_BG = "#f0f0f0"
ENTRY_BG = "#ffffff"
TEXT_COLOR = "#000000"
BTN_ACTIVE = "#d0d0d0"
STATUS_BG = "#e0e0e0"
RESP_OK = "#e0ffe0"
RESP_WARN = "#fff4e0"
RESP_ERR = "#ffe0e0"

# API modes
JSON_TYPES = ["Normal JSON", "Google JSON", "JSON-RPC"]
METHOD_IN_OPTIONS = ["Method in Path", "Method in Action", "Method in JSON Body"]

# ================= VAPIX Endpoints =================

VAPIX_ENDPOINTS = [
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
