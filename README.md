# 🏒 NHL Global Series Düsseldorf – Discord Ticket Bot

This bot checks daily for ticket information for the **NHL Global Series in Düsseldorf (December 18, 2026 & December 20, 2026)** and notifies you via Discord as soon as something new appears.

## Sources
- **Ticketmaster API** (primary) – official structured data
- **Live Nation scraper** (backup) – parses the event page directly

---

## Setup

### 1. Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Discord Bot Token → [discord.com/developers](https://discord.com/developers/applications)
- Ticketmaster API Key → [developer.ticketmaster.com](https://developer.ticketmaster.com) (free)

### 2. Install dependencies

```bash
uv sync
```

### 3. Create `.env`

```bash
cp .env.example .env
# Fill in your values
```

### 4. Discord setup

1. Enable **Developer Mode** in Discord: Settings → Advanced → Developer Mode
2. **Channel ID**: Right-click the channel → "Copy ID"
3. **User ID**: Right-click your name → "Copy ID"
4. **Invite the bot**: OAuth2 → URL Generator → Scopes: `bot` → Permissions: `Send Messages`, `Embed Links`

### 5. Run the bot

```bash
uv run python -m nhl_global_series_discord_bot.main
```

## How it works

1. Bot starts and connects to Discord
2. Immediately runs a first check on startup
3. Then checks daily at `CHECK_HOUR:00` (Europe/Berlin)
4. If something new is found → Discord embed message + @mention
5. Previously seen statuses are saved in `state.json` to avoid duplicate notifications