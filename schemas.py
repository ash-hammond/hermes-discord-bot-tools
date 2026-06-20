"""Tool schemas for hermes-discord-bot-tools."""

DISCORD_API_REQUEST = {
    "name": "discord_api_request",
    "description": (
        "Call an official Discord REST API endpoint as the configured bot. "
        "Use this for Discord bot functionality not covered by the typed tools. "
        "Path must be an API path like `/applications/@me` or `/channels/{id}/messages`; "
        "do not include a full URL. Non-GET requests require acknowledge_write_risk=true. "
        "High-risk destructive/moderation endpoints are blocked unless "
        "DISCORD_BOT_TOOLS_ALLOW_DANGEROUS=true is set. Never use user tokens/selfbots."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "method": {"type": "string", "enum": ["GET", "POST", "PATCH", "PUT", "DELETE"]},
            "path": {"type": "string", "description": "Discord API path beginning with `/`, e.g. `/applications/@me`."},
            "query": {"type": "object", "description": "Optional query parameters."},
            "json_body": {"type": "object", "description": "Optional JSON request body."},
            "acknowledge_write_risk": {"type": "boolean", "description": "Required true for POST/PATCH/PUT/DELETE."},
        },
        "required": ["method", "path"],
    },
}

DISCORD_GET_CURRENT_APPLICATION = {
    "name": "discord_get_current_application",
    "description": "Get the Discord application object associated with the configured bot token, including description/About-Me-like app text.",
    "parameters": {"type": "object", "properties": {}},
}

DISCORD_UPDATE_APPLICATION = {
    "name": "discord_update_application",
    "description": (
        "Update safe fields on the Discord application associated with the bot, especially `description` "
        "which Discord uses for a bot's visible About Me/application description."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "New application description / bot About Me text."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional app tags, max 5."},
            "custom_install_url": {"type": "string", "description": "Optional custom install URL."},
            "role_connections_verification_url": {"type": "string", "description": "Optional role connection verification URL."},
        },
    },
}

DISCORD_GET_CURRENT_BOT_USER = {
    "name": "discord_get_current_bot_user",
    "description": "Get the current bot user object via `/users/@me`.",
    "parameters": {"type": "object", "properties": {}},
}

DISCORD_UPDATE_CURRENT_BOT_USER = {
    "name": "discord_update_current_bot_user",
    "description": "Update the current bot user's username and/or avatar image data. Does not edit About Me; use discord_update_application for that.",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "New bot username."},
            "avatar": {"type": "string", "description": "Image data URI for avatar, or null to remove.", "nullable": True},
        },
    },
}

DISCORD_LIST_GUILDS = {
    "name": "discord_list_guilds",
    "description": "List guilds/servers the current bot is in.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Max guilds to return, 1-200.", "default": 100},
            "before": {"type": "string"},
            "after": {"type": "string"},
            "with_counts": {"type": "boolean", "default": False},
        },
    },
}

DISCORD_GET_GUILD = {
    "name": "discord_get_guild",
    "description": "Get a Discord guild/server by ID.",
    "parameters": {"type": "object", "properties": {"guild_id": {"type": "string"}, "with_counts": {"type": "boolean", "default": False}}, "required": ["guild_id"]},
}

DISCORD_LIST_GUILD_CHANNELS = {
    "name": "discord_list_guild_channels",
    "description": "List channels in a Discord guild/server.",
    "parameters": {"type": "object", "properties": {"guild_id": {"type": "string"}}, "required": ["guild_id"]},
}

DISCORD_GET_CHANNEL = {
    "name": "discord_get_channel",
    "description": "Get a Discord channel by ID.",
    "parameters": {"type": "object", "properties": {"channel_id": {"type": "string"}}, "required": ["channel_id"]},
}

DISCORD_SEND_MESSAGE = {
    "name": "discord_send_message",
    "description": "Send a Discord message as the bot. Supports content, embeds, allowed_mentions, and reply references.",
    "parameters": {
        "type": "object",
        "properties": {
            "channel_id": {"type": "string"},
            "content": {"type": "string"},
            "embeds": {"type": "array", "items": {"type": "object"}},
            "allowed_mentions": {"type": "object"},
            "reply_to_message_id": {"type": "string"},
        },
        "required": ["channel_id"],
    },
}

DISCORD_EDIT_MESSAGE = {
    "name": "discord_edit_message",
    "description": "Edit a message previously sent by this bot. Discord enforces bot-authored edit restrictions.",
    "parameters": {
        "type": "object",
        "properties": {"channel_id": {"type": "string"}, "message_id": {"type": "string"}, "content": {"type": "string"}, "embeds": {"type": "array", "items": {"type": "object"}}, "allowed_mentions": {"type": "object"}},
        "required": ["channel_id", "message_id"],
    },
}

DISCORD_DELETE_MESSAGE = {
    "name": "discord_delete_message",
    "description": "Delete a Discord message by channel and message ID. Use carefully; Discord permission checks apply.",
    "parameters": {"type": "object", "properties": {"channel_id": {"type": "string"}, "message_id": {"type": "string"}}, "required": ["channel_id", "message_id"]},
}

DISCORD_ADD_REACTION = {
    "name": "discord_add_reaction",
    "description": "Add a unicode or custom emoji reaction to a message as the bot. Custom emoji format: name:id.",
    "parameters": {"type": "object", "properties": {"channel_id": {"type": "string"}, "message_id": {"type": "string"}, "emoji": {"type": "string"}}, "required": ["channel_id", "message_id", "emoji"]},
}

DISCORD_REMOVE_OWN_REACTION = {
    "name": "discord_remove_own_reaction",
    "description": "Remove this bot's own reaction from a Discord message.",
    "parameters": {"type": "object", "properties": {"channel_id": {"type": "string"}, "message_id": {"type": "string"}, "emoji": {"type": "string"}}, "required": ["channel_id", "message_id", "emoji"]},
}

DISCORD_CREATE_THREAD = {
    "name": "discord_create_thread",
    "description": "Create a public thread from an existing message, or create a standalone thread in a text/forum-style channel depending on Discord channel type.",
    "parameters": {
        "type": "object",
        "properties": {
            "channel_id": {"type": "string"},
            "name": {"type": "string"},
            "message_id": {"type": "string", "description": "Optional source message ID. If provided, creates thread from that message."},
            "auto_archive_duration": {"type": "integer", "enum": [60, 1440, 4320, 10080], "default": 1440},
            "type": {"type": "integer", "description": "Optional Discord channel/thread type, e.g. 11 public thread."},
            "invitable": {"type": "boolean"},
        },
        "required": ["channel_id", "name"],
    },
}

DISCORD_UPDATE_MY_GUILD_MEMBER = {
    "name": "discord_update_my_guild_member",
    "description": "Update the current bot member profile in a guild, currently useful for changing the bot's server nickname.",
    "parameters": {"type": "object", "properties": {"guild_id": {"type": "string"}, "nick": {"type": "string", "description": "New nickname, or empty/null to reset."}}, "required": ["guild_id"]},
}
