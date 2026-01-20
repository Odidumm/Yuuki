import discord, os, json
from discord.ext import commands
from dotenv import load_dotenv

import imports.log_helper as log_helper
from imports.log_helper import LogTypes

intents = discord.Intents.all()
logger = log_helper.Logger("Main")

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

load_dotenv()
yuuki = commands.Bot(
    intents=intents,
    debug_guild=int(config["debug_guild_id"]),
    command_prefix=config["prefix"],
)
yuuki.remove_command("help")

# Start up the Yuri

logger.log("Starting up...", LogTypes.SYSTEM)

logger.log("Loading Auto starts...", LogTypes.SYSTEM)
for filename in os.listdir("auto"):
    if filename.endswith(".py"):
        auto_name = f"auto.{filename[:-3]}"
        try:
            yuuki.load_extension(auto_name)
            logger.log(f"Loaded {auto_name}", LogTypes.SUCCESS)
        except Exception as e:
            logger.log(f"Failed to load {auto_name}: {e}", LogTypes.ERROR)

logger.log("Loading Cogs...", LogTypes.SYSTEM)
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        cog_name = f"cogs.{filename[:-3]}"
        try:
            yuuki.load_extension(cog_name)
            logger.log(f"Loaded {cog_name}", LogTypes.SUCCESS)
        except Exception as e:
            logger.log(f"Failed to load {cog_name}: {e}", LogTypes.ERROR)

logger.log("Loading Yuri...", LogTypes.SYSTEM)
TOKEN = os.getenv("BOT-TOKEN")
yuuki.run(TOKEN)