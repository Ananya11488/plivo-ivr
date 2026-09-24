"""
Central configuration. Everything here is read from environment variables
(populated from a local, git-ignored .env file — see .env.example) so that
no credentials or personal phone numbers ever end up in source control.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file, if present

# --- Plivo credentials --------------------------------------------------
PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID", "")
PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN", "")

# --- Phone numbers --------------------------------------------------
PLIVO_FROM_NUMBER = os.environ.get("PLIVO_FROM_NUMBER", "")   # your Plivo number
DEFAULT_TO_NUMBER = os.environ.get("DEFAULT_TO_NUMBER", "")   # number to call
ASSOCIATE_NUMBER = os.environ.get("ASSOCIATE_NUMBER", "")     # live-associate placeholder

# --- OTP (hardcoded per assignment spec — your birthdate in DDMM) -------
OTP_CODE = os.environ.get("OTP_CODE", "")

# --- Public base URL for this app (e.g. an ngrok URL) --------------------
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")

# --- Audio clips played in the Level 2 menu ------------------------------
AUDIO_URL_EN = os.environ.get(
    "AUDIO_URL_EN", "https://s3.amazonaws.com/plivocloud/Trumpet.mp3"
)
AUDIO_URL_ES = os.environ.get(
    "AUDIO_URL_ES", "https://s3.amazonaws.com/plivocloud/Trumpet.mp3"
)
