# Plivo Voice IVR Demo — FDE Technical Assignment

A Flask application that places an outbound call via the Plivo Voice API,
authenticates the caller with a 4-digit OTP (re-prompting on failure), and
then walks the caller through a two-level IVR menu:

- **Level 1** — Language selection (English / Spanish)
- **Level 2** — Play a short audio message, or forward the call to a live
  associate

## How it works

| Step | Route | Purpose |
|---|---|---|
| Trigger | `POST /make-call` | Places the outbound call via Plivo's REST API |
| Answer  | `GET/POST /ivr/otp` | Prompts for the 4-digit OTP |
| Verify  | `GET/POST /ivr/otp/verify` | Checks OTP; re-prompts on failure |
| Menu 1  | `GET/POST /ivr/language` | English / Spanish |
| Menu 1  | `GET/POST /ivr/language/select` | Stores language, shows Level 2 |
| Menu 2  | `GET/POST /ivr/menu/select` | Plays audio or dials the associate |

All call-flow responses are returned as [Plivo XML](https://www.plivo.com/docs/voice/xml/).

## Required Plivo credentials

You need:
- **Plivo Auth ID** and **Auth Token** (from the [Plivo Console](https://console.plivo.com/dashboard/))
- A **Plivo phone number** to call *from*
- A phone number to call *to* (the number being tested)
- A **live-associate number** (placeholder is fine) for the call-forward branch

None of these are hardcoded in the source. They're loaded from a local
`.env` file (see `.env.example`), which is listed in `.gitignore` and is
**never committed to the repository**.

## Setup

1. **Clone the repo and install dependencies**
   ```bash
   git clone https://github.com/Ananya11488/plivo-ivr.git
   cd plivo-ivr
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure your credentials**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in:
   - `PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`
   - `PLIVO_FROM_NUMBER` — the Plivo number to call from
   - `DEFAULT_TO_NUMBER` — your phone number, in E.164 format (e.g. `+91XXXXXXXXXX`)
   - `ASSOCIATE_NUMBER` — the live-associate placeholder number
   - `OTP_CODE` — your birthdate in `DDMM` format (e.g. March 15 → `1503`)
   - `BASE_URL` — a public HTTPS URL for this app (see next step)

3. **Expose the app publicly** (Plivo needs to reach your webhooks)

   While testing locally, use [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 5000
   ```
   Copy the `https://...ngrok-free.app` URL it prints and set it as
   `BASE_URL` in your `.env` file (no trailing slash).

4. **Run the app**
   ```bash
   python app.py
   ```
   The app starts on `http://localhost:5000`.

## Steps to run and test

1. Start ngrok and the Flask app (steps 3–4 above), making sure `BASE_URL`
   in `.env` matches the current ngrok URL (ngrok URLs change every time
   you restart it on the free tier).
2. Trigger the call, either:
   - Open `http://localhost:5000` in a browser and click **Call me now**, or
   - `curl -X POST http://localhost:5000/make-call -H "Content-Type: application/json" -d '{}'`
     (uses `DEFAULT_TO_NUMBER` from `.env` if no number is passed)
3. Answer the call on your phone.
4. Enter an **incorrect** 4-digit OTP first — confirm the bot re-prompts.
5. Enter the **correct** OTP (your configured `DDMM` birthdate) — confirm you
   reach the language menu.
6. Press `1` for English or `2` for Spanish.
7. In the Level 2 menu, press `1` to hear the audio clip, or `2` to be
   forwarded to the associate number.

## Project structure

```
plivo-ivr/
├── app.py              # Flask routes + Plivo XML call-flow logic
├── config.py            # Loads all settings/secrets from environment variables
├── requirements.txt
├── .env.example          # Template — copy to .env and fill in real values
├── .gitignore            # Excludes .env and other local artifacts from git
└── templates/
    └── index.html        # Optional web UI to trigger the call
```

## Notes

- The OTP is intentionally static/hardcoded (per the assignment spec) — no
  database is used.
- The audio URLs default to a public Plivo demo MP3; swap `AUDIO_URL_EN` /
  `AUDIO_URL_ES` in `.env` for your own publicly hosted clips.
- The associate number is a placeholder — replace `ASSOCIATE_NUMBER` in
  `.env` with a real number if you want to test live call forwarding.

## Demo Video

[Watch the 3–5 minute demo on Loom](https://www.loom.com/share/b155cdd8a79445bd9c71e6d4b52d4c80)

  
