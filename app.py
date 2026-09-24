"""
Plivo Voice IVR Demo — Forward Deployed Engineer Technical Assignment
======================================================================

Flow
----
1. POST /make-call               -> places an outbound call to TO_NUMBER
2. GET/POST /ivr/otp              -> Plivo answer_url: asks caller for a 4-digit OTP
3. GET/POST /ivr/otp/verify       -> checks OTP, re-prompts on failure, otherwise
                                      moves to the language menu
4. GET/POST /ivr/language         -> Level 1 menu: English / Spanish
5. GET/POST /ivr/language/select  -> stores the chosen language, shows Level 2 menu
6. GET/POST /ivr/menu/select      -> Level 2: play an audio clip OR forward the
                                      call to a live associate

Call-flow responses are built as raw Plivo XML (https://www.plivo.com/docs/voice/xml/)
so the exact tags used are transparent and easy to audit/modify.

All secrets (Plivo Auth ID/Token, phone numbers, the OTP, the public base URL)
are read from environment variables (see .env.example) and are never
hardcoded or committed to source control.
"""

import os
from xml.sax.saxutils import escape

from flask import Flask, request, Response, render_template
from plivo import RestClient

from config import (
    PLIVO_AUTH_ID,
    PLIVO_AUTH_TOKEN,
    PLIVO_FROM_NUMBER,
    DEFAULT_TO_NUMBER,
    ASSOCIATE_NUMBER,
    OTP_CODE,
    BASE_URL,
    AUDIO_URL_EN,
    AUDIO_URL_ES,
)

app = Flask(__name__)
client = RestClient(auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)


def xml_response(body: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n{body}\n</Response>'
    return Response(xml, mimetype="text/xml")


def speak(text: str) -> str:
    return f"  <Speak>{escape(text)}</Speak>"


def get_digits(action: str, num_digits: int, inner: str, timeout: int = 15) -> str:
    return (
        f'  <GetDigits action="{escape(action)}" method="POST" '
        f'numDigits="{num_digits}" timeout="{timeout}" retries="1" redirect="true">\n'
        f"  {inner}\n"
        f"  </GetDigits>"
    )


def redirect(url: str) -> str:
    return f"  <Redirect>{escape(url)}</Redirect>"


# ---------------------------------------------------------------------------
# Frontend (optional) — simple page with a button to trigger the outbound call
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", default_number=DEFAULT_TO_NUMBER)


# ---------------------------------------------------------------------------
# 1. Outbound call trigger
# ---------------------------------------------------------------------------
@app.route("/make-call", methods=["POST"])
def make_call():
    if request.is_json:
        to_number = (request.json or {}).get("to_number") or DEFAULT_TO_NUMBER
    else:
        to_number = request.form.get("to_number") or DEFAULT_TO_NUMBER

    if not BASE_URL:
        return {
            "error": "BASE_URL is not configured. Set it in your .env file to your "
                     "publicly reachable URL (e.g. an ngrok URL), then restart the app."
        }, 500

    call = client.calls.create(
        from_=PLIVO_FROM_NUMBER,
        to_=to_number,
        answer_url=f"{BASE_URL}/ivr/otp",
        answer_method="GET",
    )
    return {"message": "Call initiated", "call_uuid": call.request_uuid, "to": to_number}


# ---------------------------------------------------------------------------
# 2 & 3. OTP authentication (re-prompts until correct)
# ---------------------------------------------------------------------------
def otp_prompt(message: str) -> str:
    body = get_digits(
        action=f"{BASE_URL}/ivr/otp/verify",
        num_digits=4,
        inner=speak(message),
    )
    # No input at all within the timeout -> loop back to the same prompt.
    body += "\n" + redirect(f"{BASE_URL}/ivr/otp")
    return body


@app.route("/ivr/otp", methods=["GET", "POST"])
def ivr_otp():
    return xml_response(
        otp_prompt("Welcome. Please enter your 4 digit O T P.")
    )


@app.route("/ivr/otp/verify", methods=["GET", "POST"])
def ivr_otp_verify():
    digits = request.values.get("Digits", "")

    if digits == OTP_CODE:
        return xml_response(language_menu())

    return xml_response(
        otp_prompt("Incorrect O T P. Please try again. Enter your 4 digit O T P.")
    )


# ---------------------------------------------------------------------------
# 4. Level 1 — Language selection
# ---------------------------------------------------------------------------
def language_menu() -> str:
    body = get_digits(
        action=f"{BASE_URL}/ivr/language/select",
        num_digits=1,
        inner=speak("You are authenticated. For English, press 1. Para espanol, oprima 2."),
    )
    body += "\n" + redirect(f"{BASE_URL}/ivr/language")
    return body


@app.route("/ivr/language", methods=["GET", "POST"])
def ivr_language():
    return xml_response(language_menu())


@app.route("/ivr/language/select", methods=["GET", "POST"])
def ivr_language_select():
    digit = request.values.get("Digits", "")

    if digit == "1":
        return xml_response(level2_menu("english"))
    elif digit == "2":
        return xml_response(level2_menu("spanish"))
    else:
        body = speak("Invalid selection.") + "\n" + redirect(f"{BASE_URL}/ivr/language")
        return xml_response(body)


# ---------------------------------------------------------------------------
# 5 & 6. Level 2 — Play audio OR forward to a live associate
# ---------------------------------------------------------------------------
LEVEL2_PROMPTS = {
    "english": "To hear a short message, press 1. To speak with an associate, press 2.",
    "spanish": "Para escuchar un mensaje, oprima 1. Para hablar con un asociado, oprima 2.",
}


def level2_menu(lang: str) -> str:
    body = get_digits(
        action=f"{BASE_URL}/ivr/menu/select?lang={lang}",
        num_digits=1,
        inner=speak(LEVEL2_PROMPTS[lang]),
    )
    body += "\n" + redirect(f"{BASE_URL}/ivr/language/menu-repeat?lang={lang}")
    return body


@app.route("/ivr/language/menu-repeat", methods=["GET", "POST"])
def ivr_menu_repeat():
    lang = request.args.get("lang", "english")
    return xml_response(level2_menu(lang))


@app.route("/ivr/menu/select", methods=["GET", "POST"])
def ivr_menu_select():
    lang = request.args.get("lang", "english")
    digit = request.values.get("Digits", "")

    if digit == "1":
        audio_url = AUDIO_URL_EN if lang == "english" else AUDIO_URL_ES
        body = (
            f"  <Play>{escape(audio_url)}</Play>\n"
            + speak("Thank you for calling. Goodbye.")
            + "\n  <Hangup/>"
        )
    elif digit == "2":
        body = (
            speak("Connecting you to a live associate. Please hold.")
            + "\n  <Dial>\n"
            + f"    <Number>{escape(ASSOCIATE_NUMBER)}</Number>\n"
            + "  </Dial>"
        )
    else:
        body = speak("Invalid selection.") + "\n" + redirect(
            f"{BASE_URL}/ivr/language/menu-repeat?lang={lang}"
        )

    return xml_response(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
