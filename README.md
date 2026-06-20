# hermes-discord-bot-tools

Full Discord bot REST tools for [Hermes Agent](https://hermes-agent.nousresearch.com/). This plugin exposes typed, schema-driven Discord bot tools plus a generic Discord REST escape hatch so a Hermes agent can operate a bot without falling back to shell `curl` commands or user-token/selfbot automation.

## Why this exists

Hermes has a Discord gateway for chatting, but gateway adapters are intentionally messaging-focused. They are not a full Discord bot-management SDK. This plugin adds bot-token REST tools for tasks such as:

- reading/updating the current application description (bot About Me)
- reading/updating the current bot user profile
- listing guilds and channels
- sending/editing/deleting bot messages
- adding/removing reactions
- creating public threads
- updating the bot's guild nickname
- calling arbitrary official Discord REST endpoints with `discord_api_request`

The generic REST tool is what makes the plugin "full" rather than only a fixed set of wrappers: if Discord supports an endpoint for bot tokens, the agent can call it by method and path.

## Safety model

- Uses **bot tokens only**: `Authorization: Bot $DISCORD_BOT_TOKEN`.
- Never uses Discord user tokens or selfbot APIs.
- Returns JSON strings for every result, including errors.
- Redacts common token-looking values from returned headers/bodies.
- `discord_api_request` requires `acknowledge_write_risk: true` for non-GET requests.
- High-risk destructive/moderation paths are blocked unless `DISCORD_BOT_TOOLS_ALLOW_DANGEROUS=true` is set.

High-risk paths include guild/channel deletes, bans, kicks, bulk deletes, role/member mutation through the generic tool, and webhook/token routes. Typed tools still rely on Discord permissions and the bot token you provide.

## Install

```bash
hermes plugins install ash-hammond/hermes-discord-bot-tools --enable
```

Or install from an explicit Git URL:

```bash
hermes plugins install https://github.com/ash-hammond/hermes-discord-bot-tools.git --enable
```

For local development before publication, install from a local Git URL:

```bash
hermes plugins install file:///absolute/path/to/hermes-discord-bot-tools --no-enable
```

Then set the bot token in the Hermes environment used by your gateway:

```bash
hermes config env-path
# edit that .env file and add:
DISCORD_BOT_TOKEN=your_bot_token_here
```

Restart Hermes/gateway after installing or changing env vars:

```bash
hermes gateway restart
```

## Tools

### Generic full API tool

- `discord_api_request` — call any official Discord bot REST endpoint by method + path.

Example: update application description / bot About Me:

```json
{
  "method": "PATCH",
  "path": "/applications/@me",
  "json_body": {
    "description": "transparent AI gremlin, Discord native, occasionally haunted by old lore."
  },
  "acknowledge_write_risk": true
}
```

### Application / profile

- `discord_get_current_application`
- `discord_update_application`
- `discord_get_current_bot_user`
- `discord_update_current_bot_user`

### Guilds / channels

- `discord_list_guilds`
- `discord_get_guild`
- `discord_list_guild_channels`
- `discord_get_channel`
- `discord_create_thread`
- `discord_update_my_guild_member`

### Messages / reactions

- `discord_send_message`
- `discord_edit_message`
- `discord_delete_message`
- `discord_add_reaction`
- `discord_remove_own_reaction`

## Required permissions

The bot must be in the target guild and have Discord permissions for whatever it attempts:

- messages: View Channel, Send Messages, Read Message History where applicable
- embeds: Embed Links
- reactions: Add Reactions
- threads: Create Public Threads / Send Messages in Threads
- nickname update: Change Nickname
- moderation/admin endpoints through the generic tool: matching Discord permissions plus `DISCORD_BOT_TOOLS_ALLOW_DANGEROUS=true` for the blocked high-risk route classes

## Development

```bash
python -m pytest tests -q
python -m py_compile __init__.py schemas.py tools.py
```

No runtime dependencies beyond Python stdlib.

## Notes

This plugin does not replace the Hermes Discord gateway. The gateway receives Discord messages and routes conversations. This plugin gives the agent callable tools for Discord REST operations.
