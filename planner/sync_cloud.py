from __future__ import annotations

import json
import secrets
import string
import urllib.request
from pathlib import Path

from .agopen import planner_root_path
from .cloud_export import build_cloud_data


DEFAULT_SERVER_URL = "http://127.0.0.1:8787"


def settings_path():
    return planner_root_path() / "sync_settings.json"


def random_code(length=18):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load_sync_settings():
    path = settings_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("sync_id") and data.get("upload_key"):
                data.setdefault("server_url", DEFAULT_SERVER_URL)
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return create_sync_settings()


def create_sync_settings(server_url=DEFAULT_SERVER_URL):
    data = {
        "server_url": server_url.rstrip("/"),
        "sync_id": random_code(20),
        "upload_key": random_code(32),
    }
    save_sync_settings(data)
    return data


def save_sync_settings(data):
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_sync_settings(server_url=DEFAULT_SERVER_URL):
    return create_sync_settings(server_url)


def mobile_url(settings):
    return f"{settings['server_url'].rstrip('/')}/s/{settings['sync_id']}"


def upload_mobile_cloud(settings=None):
    settings = settings or load_sync_settings()
    payload = build_cloud_data()
    payload["sync"] = {"id": settings["sync_id"]}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    url = f"{settings['server_url'].rstrip('/')}/api/sync/{settings['sync_id']}?key={settings['upload_key']}"
    request = urllib.request.Request(
        url,
        data=body,
        method="PUT",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8", errors="replace")
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(raw)
    return mobile_url(settings), len(payload["guides"])
