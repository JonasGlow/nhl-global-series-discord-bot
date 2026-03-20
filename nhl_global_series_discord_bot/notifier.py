import discord
import logging
from nhl_global_series_discord_bot.checker import TicketResult

log = logging.getLogger(__name__)

STATUS_EMOJI = {
    "onsale": "🟢",
    "presale": "🟡",
    "offsale": "🔴",
    "sold out": "❌",
    "available": "🟢",
    "unknown": "⚪",
}


def _status_emoji(status: str) -> str:
    status_lower = status.lower()
    for key, emoji in STATUS_EMOJI.items():
        if key in status_lower:
            return emoji
    return "⚪"


class Notifier:
    def __init__(self, channel: discord.TextChannel, user_id: int):
        self.channel = channel
        self.user_id = user_id

    async def send_healthcheck(self):
        embed = discord.Embed(
            title="✅ Daily Check – No Updates",
            description="No new ticket information found. Bot is running normally.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="NHL Global Series Düsseldorf Bot")

        try:
            await self.channel.send(embed=embed)
            log.info("Healthcheck message sent.")
        except discord.HTTPException as e:
            log.error(f"Error sending healthcheck message: {e}")

    async def send_alert(self, result: TicketResult):
        emoji = _status_emoji(result.status)

        embed = discord.Embed(
            title=f"🏒 NHL Ticket Update: {result.event_name}",
            url=result.url,
            color=discord.Color.blue(),
        )
        embed.add_field(name="📅 Date", value=result.event_date, inline=True)
        embed.add_field(name="📡 Source", value=result.source, inline=True)
        embed.add_field(name=f"{emoji} Status", value=result.status, inline=True)
        if result.price_info:
            embed.add_field(name="💶 Price", value=result.price_info, inline=True)
        embed.add_field(name="🔗 Link", value=result.url, inline=False)
        embed.set_footer(text="NHL Global Series Düsseldorf Bot")

        mention = f"<@{self.user_id}>"
        try:
            await self.channel.send(content=f"{mention} New ticket info!", embed=embed)
            log.info(f"Alert sent to channel {self.channel.id}")
        except discord.HTTPException as e:
            log.error(f"Error sending alert: {e}")