import discord, asyncio, json, signal, os
from discord.ext import commands
from dotenv import load_dotenv

import imports.log_helper as log_helper
from imports.log_helper import LogTypes

import imports.color_enum as colors
import imports.database as db

intents = discord.Intents.all()
logger = log_helper.Logger("System")

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

class AutoSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_called = False
        logger.log("AutoSystem initialized.", LogTypes.SYSTEM)

    @commands.Cog.listener()
    async def on_ready(self):
        # Set bot presence
        await self.bot.change_presence(
            activity=discord.Activity(
                type=getattr(discord.ActivityType, config["ActivityType"]),
                name=config["ActivityText"]
            ),
            status=getattr(discord.Status, config["ActivityStatus"])
        )
        logger.log("Presence set.", LogTypes.SYSTEM)

        # Send online notification
        embed = discord.Embed(
            title=f"{self.bot.user.name} ist online 🚀",
            description=f"{self.bot.user.name} ist jetzt bereit!",
            color=colors.get_color("info"),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        channel = self.bot.get_channel(int(config["log_channel_id"]))
        if channel:
            await channel.send(embed=embed)

        logger.log(f"{self.bot.user.name} ist online", LogTypes.SUCCESS)

        # Database setup (EINMALIG)
        if not hasattr(self.bot, "db"):
            self.bot.db = db.Database(config["db_path"])
            self.bot.db.connect()
            self.bot.db.create_tables()
            logger.log("Database connected and initialized.", LogTypes.SUCCESS)


        # Signal-Handler registrieren
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    # -------------------------------
    # Signal → Async Task
    # -------------------------------
    def _handle_signal(self, sig, frame):
        signal_name = self._resolve_signal_name(sig)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        loop.create_task(self._shutdown(signal_name))

    # -------------------------------
    # Signalname sicher ermitteln
    # -------------------------------
    @staticmethod
    def _resolve_signal_name(sig):
        if sig == signal.SIGINT:
            return "SIGINT (Ctrl+C)"
        if sig == signal.SIGTERM:
            return "SIGTERM (Terminate)"
        return f"Signal {sig}"

    # -------------------------------
    # Shutdown-Logik
    # -------------------------------
    async def _shutdown(self, reason: str):
        if self.shutdown_called:
            return
        self.shutdown_called = True

        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(int(config["log_channel_id"]))

        embed = discord.Embed(
            title="⚠️ Bot wird heruntergefahren",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="Grund", value=reason, inline=False)
        embed.add_field(name="Status", value="🔌 Verbindung wird getrennt…", inline=False)
        embed.set_footer(text="Shutdown erkannt")

        if channel:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

        await asyncio.sleep(1)

        # 🔥 HIER: DB schließen
        if hasattr(self.bot, "db"):
            try:
                self.bot.db.close()
            except Exception as e:
                logger.log(f"Error closing database: {e}", LogTypes.ERROR)

        # Discord sauber schließen
        await self.bot.close()

        # Prozess beenden (Windows-safe)
        os._exit(0)

def setup(bot):
    bot.add_cog(AutoSystem(bot))
    logger.log("AutoSystem cog loaded.", LogTypes.SYSTEM)
