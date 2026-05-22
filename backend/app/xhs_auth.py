import json
import secrets
import ssl
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass

import certifi
from fastapi import HTTPException, status

from .config import get_settings
from .utils import sha256_hex, utc_now


@dataclass
class AccessTokenState:
    token: str
    expires_at_ms: int


_ACCESS_TOKEN_CACHE: AccessTokenState | None = None
_ACCESS_TOKEN_LOCK = threading.Lock()


def build_xhs_signature(app_key: str, nonce: str, timestamp: int, secret: str) -> str:
    params = {
        "appKey": app_key,
        "nonce": nonce,
        "timeStamp": timestamp,
    }
    sorted_params = dict(sorted(params.items()))
    params_string = "&".join([f"{key}={value}" for key, value in sorted_params.items()])
    return sha256_hex(params_string + secret)


def get_cached_access_token() -> AccessTokenState | None:
    global _ACCESS_TOKEN_CACHE
    if _ACCESS_TOKEN_CACHE is None:
        return None
    now_ms = int(utc_now().timestamp() * 1000)
    if _ACCESS_TOKEN_CACHE.expires_at_ms - now_ms <= 60_000:
        return None
    return _ACCESS_TOKEN_CACHE


def fetch_access_token() -> AccessTokenState:
    settings = get_settings()
    if not settings.xhs_app_key or not settings.xhs_app_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先配置 XHS_APP_KEY 和 XHS_APP_SECRET",
        )

    nonce = secrets.token_hex(16)
    timestamp = int(utc_now().timestamp() * 1000)
    signature = build_xhs_signature(
        settings.xhs_app_key,
        nonce,
        timestamp,
        settings.xhs_app_secret,
    )
    payload = {
        "app_key": settings.xhs_app_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "signature": signature,
        "expires_in": timestamp + (3600 * 1000),
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        settings.xhs_access_token_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.xhs_request_timeout_ms / 1000,
            context=ssl_context,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"小红书 access_token 接口返回错误: {message or exc.reason}",
        ) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"无法连接小红书 access_token 接口: {exc.reason}",
        ) from exc

    success = data.get("success")
    if success is False:
        code = data.get("code")
        msg = data.get("msg") or "小红书 access_token 接口返回失败"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"小红书 access_token 接口返回失败: code={code}, msg={msg}",
        )

    payload_data = data.get("data", data)
    token = payload_data.get("access_token")
    expires_at_ms = payload_data.get("expires_in")
    if not token or not isinstance(expires_at_ms, int):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"小红书 access_token 响应格式不符合预期，返回字段: {list(data.keys())}",
        )

    return AccessTokenState(token=token, expires_at_ms=expires_at_ms)


def get_access_token() -> AccessTokenState:
    cached = get_cached_access_token()
    if cached:
        return cached

    with _ACCESS_TOKEN_LOCK:
        cached = get_cached_access_token()
        if cached:
            return cached
        state = fetch_access_token()
        global _ACCESS_TOKEN_CACHE
        _ACCESS_TOKEN_CACHE = state
        return state
