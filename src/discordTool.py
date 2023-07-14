#!/usr/bin/env python3
import requests, json

def post(webhook_url, sentence):
    headers = {"Content-Type": "application/json"}
    data = {"content": sentence}
    response = requests.post(webhook_url, json.dumps(data), headers=headers)
