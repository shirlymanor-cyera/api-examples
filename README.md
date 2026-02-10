# Cyera Datastore UI

Small web UI to call Cyera APIs with a JWT and query params.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
export CYERA_CLIENT_ID="XXXXX"
export CYERA_SECRET="XXXXX"
python datastore_ui.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Notes

- Select an endpoint (Datastores v2 or Issues v3).
- Paste your JWT in the input field.
- Edit the params JSON; empty values are ignored.
- Response JSON is displayed in the page output section.


