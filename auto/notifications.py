import discord, os, json
from discord.ext import commands
from dotenv import load_dotenv

import imports.log_helper as log_helper
from imports.log_helper import LogTypes
import imports.color_enum as color_enum

logger = log_helper.Logger("Main")

with open("config.json", "r") as f:
    config = json.load(f)

class notifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity = discord.Activity(type=getattr(discord.ActivityType, config["ActivityType"]), name=config["ActivityText"]), status = getattr(discord.Status, config["ActivityStatus"]))
        embed = discord.Embed(title="Yuri lebt wieder!", description="Yuri ist jetzt online und bereit, dir zu helfen!", color=color_enum.get_color("info"), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        channel = self.bot.get_channel(int(config["log_channel_id"]))
        if channel:
            await channel.send(embed=embed)
        logger.log("Yuri is online!", LogTypes.SUCCESS)

    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        logger.log(f"An error occurred in {event_method}: {args} {kwargs}", LogTypes.ERROR)
        embed = discord.Embed(title="An error occurred!", description=f"An error occurred in {event_method}:\nArgs: {args}\nKwargs: {kwargs}", color=color_enum.get_color("error"))
        channel = self.bot.get_channel(int(config["log_channel_id"]))
        if channel:
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(notifications(bot))