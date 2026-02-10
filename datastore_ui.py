import json
import os

from flask import Flask, request, render_template_string
import requests


API_URLS = {
    "datastores": "https://api.cyera.io/v2/datastores",
    "issues": "https://api.cyera.io/v3/issues",
}
LOGIN_URL = "https://api.cyera.io/v1/login"
DEFAULT_CLIENT_ID = os.getenv("CYERA_CLIENT_ID", "")
DEFAULT_SECRET = os.getenv("CYERA_SECRET", "")

DEFAULT_PARAMS = {
    "limit": "10",
    "offset": "0",
}

HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Cyera API Explorer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; }
      textarea, input, select { width: 100%; box-sizing: border-box; }
      textarea { min-height: 140px; }
      .row { margin-bottom: 16px; }
      .actions { display: flex; gap: 12px; flex-wrap: wrap; }
      .output { white-space: pre-wrap; background: #f7f7f7; padding: 12px; }
    </style>
  </head>
  <body>
    <h2>Cyera API Explorer</h2>
    <p>Create a JWT by adding your client ID and secret, optionally edit params, and fetch data.</p>
    <p><em>Tip:</em> Start with just limit/offset to avoid server errors.</p>
    <form method="post">
      <div class="row">
        <label>Client ID</label>
        <input name="client_id" placeholder="Client ID" value="{{ client_id }}" />
      </div>
      <div class="row">
        <label>Secret</label>
        <input name="secret" type="password" placeholder="Secret" value="{{ secret }}" />
      </div>
      <div class="row actions">
        <button type="submit" name="action" value="login">Create JWT</button>
      </div>
      <hr />
      <div class="row">
        <label>JWT</label>
        <textarea name="jwt" placeholder="Paste JWT here...">{{ jwt }}</textarea>
      </div>
      <div class="row">
        <label>Query Params (JSON)</label>
        <textarea name="params">{{ params }}</textarea>
      </div>
      <div class="row actions">
        <button type="submit" name="action" value="datastores">Fetch Datastores</button>
        <button type="submit" name="action" value="issues">Fetch Issues</button>
      </div>
    </form>

    {% if error %}
      <h3>Error</h3>
      <div class="output">{{ error }}</div>
    {% endif %}

    {% if response %}
      <h3>Response</h3>
      <div class="output">{{ response }}</div>
    {% endif %}
  </body>
</html>
"""

app = Flask(__name__)


def sanitize_params(raw_params):
    if not raw_params:
        return {}
    cleaned = {}
    for key, value in raw_params.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        cleaned[key] = value
    return cleaned


@app.route("/", methods=["GET", "POST"])
def index():
    jwt = ""
    endpoint = "datastores"
    client_id = DEFAULT_CLIENT_ID
    secret = DEFAULT_SECRET
    params_text = json.dumps(DEFAULT_PARAMS, indent=2)
    response_text = ""
    error_text = ""

    if request.method == "POST":
        action = request.form.get("action", "").strip()
        client_id = request.form.get("client_id", "").strip()
        secret = request.form.get("secret", "").strip()
        jwt = request.form.get("jwt", "").strip()
        params_text = request.form.get("params", "").strip() or "{}"

        if action == "login":
            if not client_id or not secret:
                error_text = "Missing client ID or secret."
            else:
                try:
                    response = requests.post(
                        LOGIN_URL,
                        headers={"Content-Type": "application/json"},
                        json={"clientId": client_id, "secret": secret},
                        timeout=30,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    jwt = payload.get("jwt") or payload.get("token") or ""
                    response_text = json.dumps(payload, indent=2)
                    if not jwt:
                        error_text = "Login succeeded but JWT was not found in response."
                except requests.HTTPError as exc:
                    detail = exc.response.text if exc.response is not None else str(exc)
                    error_text = f"HTTP error: {exc}\n\n{detail}"
                except requests.RequestException as exc:
                    error_text = f"Request failed: {exc}"
                except ValueError:
                    error_text = "Response was not valid JSON."
        else:
            endpoint = action or "datastores"
            if endpoint not in API_URLS:
                error_text = "Invalid endpoint selection."
            elif not jwt:
                error_text = "Missing JWT. Please paste a token."
            else:
                try:
                    parsed_params = json.loads(params_text)
                    if not isinstance(parsed_params, dict):
                        raise ValueError("Params JSON must be an object.")
                except (json.JSONDecodeError, ValueError) as exc:
                    error_text = f"Could not parse JSON:\n{exc}"
                else:
                    headers = {"Authorization": f"Bearer {jwt}"}
                    params = sanitize_params(parsed_params)
                    try:
                        url = API_URLS[endpoint]
                        response = requests.get(
                            url, headers=headers, params=params, timeout=30
                        )
                        response.raise_for_status()
                        response_text = json.dumps(response.json(), indent=2)
                    except requests.HTTPError as exc:
                        detail = exc.response.text if exc.response is not None else str(exc)
                        error_text = f"HTTP error: {exc}\n\n{detail}"
                    except requests.RequestException as exc:
                        error_text = f"Request failed: {exc}"
                    except ValueError:
                        error_text = "Response was not valid JSON."

    return render_template_string(
        HTML,
        jwt=jwt,
        endpoint=endpoint,
        client_id=client_id,
        secret=secret,
        params=params_text,
        response=response_text,
        error=error_text,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
