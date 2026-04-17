import json
import os
import urllib.request


def send_slack(message):
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return "Webhook URL not set"

    data = {"text": message}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        return str(e)
