import os
import json
import random
import secrets
import uuid
import copy

# ---------------- Configuration ----------------
JSON_FOLDER = "json_configs"
PRESETS_FILE = "presets.json"
ID_RPC = "helmut"
GOOGLE_CONTEXT = "test12345"
def generate_uuid_list(count=1):
    return [str(uuid.uuid4()) for _ in range(count)]
# ---------------- Endpoints ----------------
GET_ENDPOINTS = [
    "/vapix/intercom/GetContacts",
    "/vapix/call/GetSIPAccount",
    "/vapix/call/GetSIPAccounts",
    "/vapix/call/GetSIPAccountStatus",
    "/vapix/call/GetServiceCapabilities",
    "/vapix/call/GetSupportedSIPAccountAttributes",
    "/vapix/call/GetSupportedSIPConfigurationAttributes",
    "/vapix/call/GetSIPConfiguration",
    "/vapix/call/GetSupportedMediaEncryptionModes",
    "/vapix/call/GetDefaultAudioCodecs",
    "/vapix/call/GetSupportedAudioCodecs",
    "/vapix/call/GetAudioCodecs",
    "/vapix/call/GetCallStatus"
]

SET_ENDPOINTS = [
    "/vapix/call/SetSIPAccount",
    "/vapix/call/SetSIPAccounts",
    "/vapix/call/SetSIPConfiguration",
    "/vapix/call/SetAudioCodecs",
    "/vapix/call/Call",
    "/vapix/call/TerminateCall",
    "/vapix/intercom/SetContacts"
]

REMOVE_ENDPOINTS = [
    "/vapix/call/RemoveSIPAccount",
    "/vapix/call/RemoveSIPAccounts",
    "/vapix/intercom/RemoveContacts"
]

SPECIAL_PARAMS = {
    "GetSIPAccountStatus": {"SIPAccountId": "sip_account_0"},
    "GetSIPAccount": {"SIPAccountId": "sip_account_0"},
    "GetCallStatus": {"CallId": "Out-18-18-SIP"},
}

REMOVE_PAYLOADS = {
    "RemoveSIPAccount": {"SIPAccountId": "sip_account_0"},
    "RemoveSIPAccounts": {"SIPAccountId": ["sip_account_0", "sip_account_1"]},
    "RemoveContacts": {"ids": generate_uuid_list()}
}
summary = {
    "normal": 0,
    "unhappy_no_data": 0,
    "unhappy_invalid": 0,
    "unhappy_wrong_type": 0,
    "unhappy_fuzz": 0,
}



# ---------------- SET Payloads ----------------
def random_sip_account():
    return {
        "UserId": f"user{random.randint(1000,9999)}",
        "Password": secrets.token_hex(8),
        "Registrar": f"192.168.0.{random.randint(1,254)}",
        "PublicDomain": f"example{random.randint(1,100)}.axis.com"
    }

def generate_set_contacts_payload_random():
    first_name = f"Tester {random.randint(1,99):02d}"
    contact_id = str(uuid.uuid4())
    sip_address = f"192168{random.randint(1000,9999)}"
    sip_account_id = f"sip_account_{random.randint(0,9)}"
    return {
        "id": contact_id,
        "type": "Person",
        "firstName": first_name,
        "lastName": "",
        "callInformation": [{"type":"SIP","address":sip_address,"accountid":sip_account_id}],
        "callForkingType":"sequential",
        "UIAttributes":[{"Name":"DisplayName","Value":first_name}]
    }

SET_PAYLOADS = {
    "SetSIPAccount": {"SIPAccount": random_sip_account()},
    "SetSIPAccounts": {"SIPAccounts": {"SIPAccount":[random_sip_account(), random_sip_account()]}},
    "SetSIPConfiguration": {"SIPConfiguration": {"SIPEnabled": True}},
    "SetAudioCodecs":{"AudioCodec":[{"Name":"G.722","SampleRate":16000}]},
    "SetContacts":{"contacts":[generate_set_contacts_payload_random()]},
    "TerminateCall":{"CallId": "Out-18-18-SIP"},
    "Call":{"To": "sip:10.27.35.8:5060"}
}

# ---------------- Helpers ----------------
def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ---------- recursive unhappy ----------
def make_unhappy_payload(data):
    if isinstance(data, dict):
        return {k: make_unhappy_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return []
    if isinstance(data, str):
        return ""
    if isinstance(data, (int, float)):
        return -1
    return None


def make_invalid_payload(data):
    if isinstance(data, dict):
        return {k: make_invalid_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return ["INVALID"]
    if isinstance(data, str):
        return "INVALID"
    if isinstance(data, (int, float)):
        return -999
    return "INVALID"


# ---------------- Create folders ----------------
sections = ["get","set","remove"]
subfolders = ["normal_path","normal_action","normal_body","google","rpc"]

for sec in sections:
    for sub in subfolders:
        os.makedirs(os.path.join(JSON_FOLDER, sec, sub), exist_ok=True)
    os.makedirs(os.path.join(JSON_FOLDER, sec, "unhappy"), exist_ok=True)


# ---------------- Create presets ----------------
def create_presets(endpoints, payloads, section):
    presets = []

    formats = {
        "Normal_Path":"normal_path",
        "Normal_Action":"normal_action",
        "Normal_Body":"normal_body",
        "Google":"google",
        "RPC":"rpc"
    }

    for endpoint in endpoints:
        method = endpoint.split("/")[-1]
        params = payloads.get(method, {})

        for fmt, subfolder in formats.items():
            file_name = f"{method}_{fmt}.json"
            file_path = os.path.join(JSON_FOLDER, section, subfolder, file_name)
            json_file_relative = os.path.relpath(file_path, JSON_FOLDER).replace("\\", "/")

            if fmt=="Normal_Body":
                payload = {method: params}
            elif fmt=="Google":
                payload = {"apiVersion":"1.5","method":method,"params":params,"context":GOOGLE_CONTEXT}
            elif fmt=="RPC":
                payload = {"jsonrpc":"2.0","method":method,"params":params,"id":ID_RPC}
            else:
                payload = params

            save_json(file_path, payload)

            endpoint_url = (
                f"{endpoint}?action={method}" if fmt=="Normal_Action"
                else endpoint if fmt=="Normal_Path"
                else "/".join(endpoint.split("/")[:-1])
            )
            summary["normal"] += 1
            presets.append({
                "name": f"{method}_{fmt}",
                "endpoint": endpoint_url,
                "json_file": json_file_relative,
                "simple_format": False,
                "json_type": "normal" if fmt.startswith("Normal") else fmt.lower()
            })

    return presets

def make_fuzz_payload(data):
    fuzz_strings = [
        "A" * 5000,
        "<script>alert(1)</script>",
        "' OR 1=1 --",
        "\x00\x01\x02",
        "漢字🚀",
    ]

    fuzz_numbers = [
        0,
        -1,
        999999999999999999,
        float("inf"),
        float("-inf"),
    ]

    if isinstance(data, dict):
        return {k: make_fuzz_payload(v) for k, v in data.items()}

    if isinstance(data, list):
        if data:
            return [make_fuzz_payload(data[0])]
        return [None]

    if isinstance(data, str):
        return random.choice(fuzz_strings)

    if isinstance(data, (int, float)):
        return random.choice(fuzz_numbers)

    if isinstance(data, bool):
        return "TRUEEEEE"

    return None

def make_wrong_type_payload(data):
    if isinstance(data, dict):
        return {k: make_wrong_type_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return "WRONG_TYPE"          # list → string
    if isinstance(data, str):
        return 12345                 # string → number
    if isinstance(data, (int, float)):
        return "NOT_A_NUMBER"        # number → string
    if isinstance(data, bool):
        return "true"                # bool → string
    return None


# ---------------- Create unhappy presets ----------------
def create_unhappy_tests(endpoints, payloads):

    unhappy_presets = []

    for endpoint in endpoints:
        method = endpoint.split("/")[-1]
        params = payloads.get(method) or SPECIAL_PARAMS.get(method)

        if not params:
            continue  # skip endpoints without params

        section = (
            "get" if endpoint in GET_ENDPOINTS
            else "set" if endpoint in SET_ENDPOINTS
            else "remove"
        )

        folder = os.path.join(JSON_FOLDER, section, "unhappy")

        # ---- NO DATA ----
        no_data = make_unhappy_payload(params)
        no_data_file = os.path.join(folder, f"{method}_unhappy_no_data.json")
        save_json(no_data_file, no_data)
        # store relative path
        json_file_relative = os.path.relpath(no_data_file, JSON_FOLDER).replace("\\", "/")

        unhappy_presets.append({
            "name": f"{method}_unhappy_no_data",
            "endpoint": endpoint,
            "json_file": json_file_relative,
            "simple_format": False,
            "json_type": "normal"
        })
        summary["unhappy_no_data"] += 1


        # ---- INVALID DATA ----
        invalid = make_invalid_payload(params)
        invalid_file = os.path.join(folder, f"{method}_unhappy_invalid_data.json")
        save_json(invalid_file, invalid)
        json_file_relative = os.path.relpath(invalid_file, JSON_FOLDER).replace("\\", "/")

        unhappy_presets.append({
            "name": f"{method}_unhappy_invalid_data",
            "endpoint": endpoint,
            "json_file": json_file_relative,
            "simple_format": False,
            "json_type": "normal"
        })
        summary["unhappy_invalid"] += 1


        # ---- WRONG DATATYPE ----
        wrong_type = make_wrong_type_payload(params)
        wrong_type_file = os.path.join(folder, f"{method}_unhappy_wrong_type.json")
        save_json(wrong_type_file, wrong_type)
        json_file_relative = os.path.relpath(wrong_type_file, JSON_FOLDER).replace("\\", "/")

        unhappy_presets.append({
            "name": f"{method}_unhappy_wrong_type",
            "endpoint": endpoint,
            "json_file": json_file_relative,
            "simple_format": False,
            "json_type": "normal"
        })
        summary["unhappy_wrong_type"] += 1


        # ---- FUZZ DATA ----
        fuzz = make_fuzz_payload(params)
        fuzz_file = os.path.join(folder, f"{method}_unhappy_fuzz.json")
        save_json(fuzz_file, fuzz)
        json_file_relative = os.path.relpath(fuzz_file, JSON_FOLDER).replace("\\", "/")

        unhappy_presets.append({
            "name": f"{method}_unhappy_fuzz",
            "endpoint": endpoint,
            "json_file": json_file_relative,
            "simple_format": False,
            "json_type": "normal"
        })
        summary["unhappy_fuzz"] += 1

    return unhappy_presets


# ---------------- Generate ----------------
all_presets = []

all_presets += create_presets(GET_ENDPOINTS, SPECIAL_PARAMS, "get")
all_presets += create_presets(SET_ENDPOINTS, SET_PAYLOADS, "set")
all_presets += create_presets(REMOVE_ENDPOINTS, REMOVE_PAYLOADS, "remove")

all_presets += create_unhappy_tests(
    GET_ENDPOINTS + SET_ENDPOINTS + REMOVE_ENDPOINTS,
    {**SET_PAYLOADS, **SPECIAL_PARAMS, **REMOVE_PAYLOADS}
)

with open(PRESETS_FILE, "w", encoding="utf-8") as f:
    json.dump(all_presets, f, indent=2)

total_tests = sum(summary.values())

print("✅ Presets + unhappy variants generated successfully")
print("📊 TEST GENERATION SUMMARY")
print(f"   Normal tests:        {summary['normal']}")
print(f"   Unhappy no data:     {summary['unhappy_no_data']}")
print(f"   Unhappy invalid:     {summary['unhappy_invalid']}")
print(f"   Unhappy wrong type:  {summary['unhappy_wrong_type']}")
print(f"   Unhappy fuzz:        {summary['unhappy_fuzz']}")
print(f"   TOTAL TESTS:         {total_tests}")