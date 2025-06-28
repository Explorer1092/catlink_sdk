"""Constants for CatLink SDK."""

# API Configuration
DEFAULT_API_BASE = "https://app.catlinks.cn/api/"
DEFAULT_LANGUAGE = "zh_CN"

# Authentication Keys
SIGN_KEY = "00109190907746a7ad0e2139b6d09ce47551770157fe4ac5922f3a5454c82712"
RSA_PUBLIC_KEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCCA9I+iEl2AI8dnhdwwxPxHVK8iNAt6aTq6UhNsLsguWS5qtbLnuGz2RQdfNS"
    "aKSU2B6D/vE2gb1fM6f1A5cKndqF/riWGWn1EfL3FFQZduOTxoA0RTQzhrTa5LHcJ/an/NuHUwShwIOij0Mf4g8faTe4FT7/HdA"
    "oK7uW0cG9mZwIDAQAB"
)

# Device Types
DEVICE_TYPE_SCOOPER = "SCOOPER"
DEVICE_TYPE_LITTER_BOX_599 = "LITTER_BOX_599"
DEVICE_TYPE_FEEDER = "FEEDER"
DEVICE_TYPE_WATER_FOUNTAIN = "WATER_FOUNTAIN"

# Device Modes
MODE_AUTO = "auto"
MODE_MANUAL = "manual"
MODE_TIME = "time"

# Device Actions
ACTION_START = "start"
ACTION_PAUSE = "pause"
ACTION_CLEAN = "clean"

# API Endpoints
API_LOGIN = "login/password"
API_DEVICE_LIST = "token/device/union/list/sorted"
API_DEVICE_INFO = "token/device/info"
API_DEVICE_CHANGE_MODE = "token/device/changeMode"
API_DEVICE_ACTION = "token/device/actionCmd"
API_FEEDER_DETAIL = "token/device/feeder/detail"
API_CAT_TOILET_EVENT_LOG = "token/catToilet/event/log"

# Return Codes
RETURN_CODE_SUCCESS = 0
RETURN_CODE_ILLEGAL_TOKEN = 1002

# Device States
STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_NEED_RESET = "need_reset"

# Work Status Codes
WORK_STATUS_IDLE = "00"
WORK_STATUS_RUNNING = "01"
WORK_STATUS_NEED_RESET = "02"

# Garbage Status Codes
GARBAGE_STATUS_NORMAL = "00"
GARBAGE_STATUS_MOVEMENT_STARTED = "02"
GARBAGE_STATUS_MOVING = "03"

# Error Messages
ERROR_DEVICE_ONLINE = "device online"

# Other Constants
PLATFORM_ANDROID = "ANDROID"