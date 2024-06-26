#Utilities for SuperLink

import requests
from config import Config

def trigger_zap(payload):
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(Config.ZAPIER_WEBHOOK_URL, json=payload, headers=headers)
    return response.status_code, response.json()
