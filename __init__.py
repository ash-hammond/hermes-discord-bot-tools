"""Hermes plugin registration for Discord bot REST tools."""

try:
    from . import schemas, tools
except ImportError:  # allow loading from a bare plugin directory
    import schemas  # type: ignore[no-redef]
    import tools  # type: ignore[no-redef]

_TOOLS = [
    ("discord_api_request", schemas.DISCORD_API_REQUEST, tools.discord_api_request),
    ("discord_get_current_application", schemas.DISCORD_GET_CURRENT_APPLICATION, tools.discord_get_current_application),
    ("discord_update_application", schemas.DISCORD_UPDATE_APPLICATION, tools.discord_update_application),
    ("discord_get_current_bot_user", schemas.DISCORD_GET_CURRENT_BOT_USER, tools.discord_get_current_bot_user),
    ("discord_update_current_bot_user", schemas.DISCORD_UPDATE_CURRENT_BOT_USER, tools.discord_update_current_bot_user),
    ("discord_list_guilds", schemas.DISCORD_LIST_GUILDS, tools.discord_list_guilds),
    ("discord_get_guild", schemas.DISCORD_GET_GUILD, tools.discord_get_guild),
    ("discord_list_guild_channels", schemas.DISCORD_LIST_GUILD_CHANNELS, tools.discord_list_guild_channels),
    ("discord_get_channel", schemas.DISCORD_GET_CHANNEL, tools.discord_get_channel),
    ("discord_send_message", schemas.DISCORD_SEND_MESSAGE, tools.discord_send_message),
    ("discord_edit_message", schemas.DISCORD_EDIT_MESSAGE, tools.discord_edit_message),
    ("discord_delete_message", schemas.DISCORD_DELETE_MESSAGE, tools.discord_delete_message),
    ("discord_add_reaction", schemas.DISCORD_ADD_REACTION, tools.discord_add_reaction),
    ("discord_remove_own_reaction", schemas.DISCORD_REMOVE_OWN_REACTION, tools.discord_remove_own_reaction),
    ("discord_create_thread", schemas.DISCORD_CREATE_THREAD, tools.discord_create_thread),
    ("discord_update_my_guild_member", schemas.DISCORD_UPDATE_MY_GUILD_MEMBER, tools.discord_update_my_guild_member),
]


def register(ctx):
    for name, schema, handler in _TOOLS:
        ctx.register_tool(name=name, toolset="discord", schema=schema, handler=handler)
