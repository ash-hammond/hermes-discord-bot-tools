"""Tool handlers for hermes-discord-bot-tools."""

from __future__ import annotations

import json
import os
import re
import traceback
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DISCORD_BOT_TOKEN_ENV = "DISCORD_BOT_TOKEN"
ALLOW_DANGEROUS_ENV = "DISCORD_BOT_TOOLS_ALLOW_DANGEROUS"
API_BASE_ENV = "DISCORD_BOT_TOOLS_API_BASE"
DEFAULT_API_BASE = "https://discord.com/api/v10"

_TOKEN_RE = re.compile(r"(mfa\.[A-Za-z0-9_-]{20,}|[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27,})")
SNOWFLAKE_RE = re.compile(r"^\d{5,25}$")

DANGEROUS_PATH_PATTERNS = [
    re.compile(r"^/guilds/\d+$"),
    re.compile(r"^/channels/\d+$"),
    re.compile(r"^/guilds/\d+/bans(?:/|$)"),
    re.compile(r"^/guilds/\d+/members/\d+$"),
    re.compile(r"^/guilds/\d+/members/\d+/roles/"),
    re.compile(r"^/guilds/\d+/roles(?:/|$)"),
    re.compile(r"^/channels/\d+/messages/bulk-delete$"),
    re.compile(r"^/webhooks/"),
]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _redact(obj: Any) -> Any:
    if isinstance(obj, str):
        return _TOKEN_RE.sub("[REDACTED_TOKEN]", obj)
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in {"authorization", "token", "bot_token", "access_token"}:
                out[k] = "[REDACTED]"
            else:
                out[k] = _redact(v)
        return out
    return obj


def _err(message: str, **extra: Any) -> str:
    payload = {"success": False, "error": message}
    payload.update(extra)
    return _json(_redact(payload))


def _safe(fn):
    def wrapper(args: dict | None = None, **kwargs: Any) -> str:
        try:
            return fn(args or {}, **kwargs)
        except Exception as exc:  # defensive plugin boundary
            return _err("Unhandled plugin error", exception=str(exc), traceback=traceback.format_exc(limit=3))
    return wrapper


def _token() -> tuple[str | None, str | None]:
    tok = os.environ.get(DISCORD_BOT_TOKEN_ENV, "").strip()
    if not tok:
        return None, f"Missing {DISCORD_BOT_TOKEN_ENV}; set it in the Hermes gateway environment/.env"
    if tok.lower().startswith("bot "):
        tok = tok[4:].strip()
    return tok, None


def _api_base() -> str:
    return os.environ.get(API_BASE_ENV, DEFAULT_API_BASE).rstrip("/")


def _require_snowflake(args: dict, name: str) -> tuple[str | None, str | None]:
    val = args.get(name)
    if not isinstance(val, str) or not val.strip():
        return None, f"`{name}` is required"
    val = val.strip()
    if not SNOWFLAKE_RE.match(val):
        return None, f"`{name}` must be a Discord snowflake ID string"
    return val, None


def _clean_path(path: str) -> tuple[str | None, str | None]:
    if not isinstance(path, str) or not path.strip():
        return None, "`path` is required"
    path = path.strip()
    if path.startswith("http://") or path.startswith("https://") or "discord.com/api" in path:
        return None, "Use an API path like `/applications/@me`, not a full URL"
    if not path.startswith("/"):
        return None, "`path` must start with `/`"
    if ".." in path or "\n" in path or "\r" in path:
        return None, "Invalid path"
    return path, None


def _is_dangerous(method: str, path: str) -> bool:
    if method == "GET":
        return False
    return any(p.search(path) for p in DANGEROUS_PATH_PATTERNS)


def _dangerous_allowed() -> bool:
    return os.environ.get(ALLOW_DANGEROUS_ENV, "").strip().lower() == "true"


def _request(method: str, path: str, *, query: dict | None = None, body: Any = None) -> tuple[Any, dict]:
    method = method.upper().strip()
    if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
        return None, {"success": False, "error": f"Unsupported method {method}"}
    clean_path, path_err = _clean_path(path)
    if path_err:
        return None, {"success": False, "error": path_err}
    assert clean_path is not None

    tok, tok_err = _token()
    if tok_err:
        return None, {"success": False, "error": tok_err}
    assert tok is not None

    url = _api_base() + clean_path
    if query:
        q = {k: v for k, v in query.items() if v is not None}
        if q:
            url += "?" + urllib.parse.urlencode(q, doseq=True)

    data = None
    headers = {
        "Authorization": f"Bot {tok}",
        "User-Agent": "hermes-discord-bot-tools/0.1 (+https://github.com/ash/hermes-discord-bot-tools)",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            parsed = json.loads(raw) if raw.strip() else None
            meta = {"success": True, "status": resp.status, "headers": _interesting_headers(resp.headers)}
            return parsed, meta
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw) if raw.strip() else raw
        except json.JSONDecodeError:
            parsed = raw
        return None, _redact({"success": False, "status": e.code, "error": f"Discord API error {e.code}", "body": parsed, "headers": _interesting_headers(e.headers)})
    except urllib.error.URLError as e:
        return None, {"success": False, "error": f"Network error: {e}"}


def _interesting_headers(headers: Any) -> dict[str, str]:
    wanted = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset-after", "retry-after", "content-type"]
    return {h: headers.get(h) for h in wanted if headers.get(h) is not None}


def _body_from_fields(args: dict, fields: list[str]) -> dict:
    return {k: args[k] for k in fields if k in args}


def _emoji_path(emoji: str) -> str:
    if not isinstance(emoji, str) or not emoji.strip():
        raise ValueError("`emoji` is required")
    emoji = emoji.strip()
    if ":" in emoji and not (emoji.startswith("<") and emoji.endswith(">")):
        # name:id -> name:id, just URL-encode as one path segment
        pass
    return urllib.parse.quote(emoji, safe="")


def _result(data: Any, meta: dict, **extra: Any) -> str:
    if not meta.get("success"):
        return _json(_redact(meta))
    payload = {"success": True, "status": meta.get("status"), "data": data}
    payload.update(extra)
    if meta.get("headers"):
        payload["headers"] = meta["headers"]
    return _json(_redact(payload))


@_safe
def discord_api_request(args: dict, **kwargs: Any) -> str:
    method = str(args.get("method", "GET")).upper().strip()
    path, path_err = _clean_path(args.get("path", ""))
    if path_err:
        return _err(path_err)
    assert path is not None
    if method != "GET" and args.get("acknowledge_write_risk") is not True:
        return _err("Non-GET Discord API calls require acknowledge_write_risk=true")
    if _is_dangerous(method, path) and not _dangerous_allowed():
        return _err(
            f"Blocked high-risk Discord endpoint by default. Set {ALLOW_DANGEROUS_ENV}=true to allow it.",
            method=method,
            path=path,
        )
    data, meta = _request(method, path, query=args.get("query"), body=args.get("json_body"))
    return _result(data, meta, method=method, path=path)


@_safe
def discord_get_current_application(args: dict, **kwargs: Any) -> str:
    data, meta = _request("GET", "/applications/@me")
    return _result(data, meta)


@_safe
def discord_update_application(args: dict, **kwargs: Any) -> str:
    allowed = ["description", "tags", "custom_install_url", "role_connections_verification_url"]
    body = _body_from_fields(args, allowed)
    if not body:
        return _err("Provide at least one application field to update", allowed_fields=allowed)
    if "description" in body and not isinstance(body["description"], str):
        return _err("`description` must be a string")
    data, meta = _request("PATCH", "/applications/@me", body=body)
    return _result(data, meta)


@_safe
def discord_get_current_bot_user(args: dict, **kwargs: Any) -> str:
    data, meta = _request("GET", "/users/@me")
    return _result(data, meta)


@_safe
def discord_update_current_bot_user(args: dict, **kwargs: Any) -> str:
    body = _body_from_fields(args, ["username", "avatar"])
    if not body:
        return _err("Provide `username` and/or `avatar`")
    data, meta = _request("PATCH", "/users/@me", body=body)
    return _result(data, meta)


@_safe
def discord_list_guilds(args: dict, **kwargs: Any) -> str:
    query = {
        "limit": max(1, min(int(args.get("limit") or 100), 200)),
        "before": args.get("before"),
        "after": args.get("after"),
        "with_counts": str(bool(args.get("with_counts", False))).lower(),
    }
    data, meta = _request("GET", "/users/@me/guilds", query=query)
    return _result(data, meta)


@_safe
def discord_get_guild(args: dict, **kwargs: Any) -> str:
    guild_id, err = _require_snowflake(args, "guild_id")
    if err:
        return _err(err)
    data, meta = _request("GET", f"/guilds/{guild_id}", query={"with_counts": str(bool(args.get("with_counts", False))).lower()})
    return _result(data, meta)


@_safe
def discord_list_guild_channels(args: dict, **kwargs: Any) -> str:
    guild_id, err = _require_snowflake(args, "guild_id")
    if err:
        return _err(err)
    data, meta = _request("GET", f"/guilds/{guild_id}/channels")
    return _result(data, meta)


@_safe
def discord_get_channel(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    data, meta = _request("GET", f"/channels/{channel_id}")
    return _result(data, meta)


@_safe
def discord_send_message(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    body = _body_from_fields(args, ["content", "embeds", "allowed_mentions"])
    if args.get("reply_to_message_id"):
        body["message_reference"] = {"message_id": args["reply_to_message_id"], "channel_id": channel_id}
    if not body.get("content") and not body.get("embeds"):
        return _err("Provide `content` and/or `embeds`")
    data, meta = _request("POST", f"/channels/{channel_id}/messages", body=body)
    return _result(data, meta)


@_safe
def discord_edit_message(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    message_id, err = _require_snowflake(args, "message_id")
    if err:
        return _err(err)
    body = _body_from_fields(args, ["content", "embeds", "allowed_mentions"])
    if not body:
        return _err("Provide `content`, `embeds`, and/or `allowed_mentions`")
    data, meta = _request("PATCH", f"/channels/{channel_id}/messages/{message_id}", body=body)
    return _result(data, meta)


@_safe
def discord_delete_message(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    message_id, err = _require_snowflake(args, "message_id")
    if err:
        return _err(err)
    data, meta = _request("DELETE", f"/channels/{channel_id}/messages/{message_id}")
    return _result(data, meta, channel_id=channel_id, message_id=message_id)


@_safe
def discord_add_reaction(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    message_id, err = _require_snowflake(args, "message_id")
    if err:
        return _err(err)
    try:
        emoji = _emoji_path(args.get("emoji", ""))
    except ValueError as exc:
        return _err(str(exc))
    data, meta = _request("PUT", f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")
    return _result(data, meta)


@_safe
def discord_remove_own_reaction(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    message_id, err = _require_snowflake(args, "message_id")
    if err:
        return _err(err)
    try:
        emoji = _emoji_path(args.get("emoji", ""))
    except ValueError as exc:
        return _err(str(exc))
    data, meta = _request("DELETE", f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")
    return _result(data, meta)


@_safe
def discord_create_thread(args: dict, **kwargs: Any) -> str:
    channel_id, err = _require_snowflake(args, "channel_id")
    if err:
        return _err(err)
    name = args.get("name")
    if not isinstance(name, str) or not name.strip():
        return _err("`name` is required")
    body = {"name": name.strip(), "auto_archive_duration": int(args.get("auto_archive_duration") or 1440)}
    if args.get("type") is not None:
        body["type"] = int(args["type"])
    if args.get("invitable") is not None:
        body["invitable"] = bool(args["invitable"])
    message_id = args.get("message_id")
    if message_id:
        if not isinstance(message_id, str) or not SNOWFLAKE_RE.match(message_id):
            return _err("`message_id` must be a Discord snowflake if provided")
        path = f"/channels/{channel_id}/messages/{message_id}/threads"
    else:
        path = f"/channels/{channel_id}/threads"
    data, meta = _request("POST", path, body=body)
    return _result(data, meta)


@_safe
def discord_update_my_guild_member(args: dict, **kwargs: Any) -> str:
    guild_id, err = _require_snowflake(args, "guild_id")
    if err:
        return _err(err)
    body: dict[str, Any] = {}
    if "nick" in args:
        body["nick"] = args.get("nick")
    if not body:
        return _err("Provide `nick` (string or null/empty to reset if Discord accepts it)")
    data, meta = _request("PATCH", f"/guilds/{guild_id}/members/@me", body=body)
    return _result(data, meta)
