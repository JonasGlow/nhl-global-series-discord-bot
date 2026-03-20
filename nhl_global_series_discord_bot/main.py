import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio

from nhl_global_series_discord_bot.checker import TicketChecker
from nhl_global_series_discord_bot.notifier import Notifier
from nhl_global_series_discord_bot.utils.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


class NHLBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.scheduler = AsyncIOScheduler()
        self.checker = TicketChecker()
        self.notifier: Notifier | None = None

    async def setup_hook(self):
        log.info("Bot wird gestartet...")

    async def on_ready(self):
        log.info(f"Eingeloggt als {self.user} (ID: {self.user.id})")

        channel = self.get_channel(settings.discord_channel_id)
        if channel is None:
            log.error(f"Channel {settings.discord_channel_id} nicht gefunden!")
            return

        self.notifier = Notifier(channel, settings.discord_user_id)

        # Scheduler starten
        self.scheduler.add_job(
            self.run_check,
            CronTrigger(hour=settings.check_hour, minute=0, timezone="Europe/Berlin"),
            id="daily_check",
            replace_existing=True,
        )
        self.scheduler.start()
        log.info(f"Scheduler läuft – täglicher Check um {settings.check_hour}:00 Uhr")

        # Beim Start direkt einmal prüfen
        await self.run_check()

    async def run_check(self):
        log.info("Starting ticket check...")
        try:
            results = await self.checker.check_all()
            if results:
                log.info(f"{len(results)} new result(s) found!")
                for result in results:
                    await self.notifier.send_alert(result)
            else:
                log.info("No new ticket info found.")
                await self.notifier.send_healthcheck()
        except Exception as e:
            log.error(f"Error during check: {e}", exc_info=True)


async def main():
    bot = NHLBot()
    async with bot:
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())