import discord, os, json
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from dotenv import load_dotenv

import imports.log_helper as log_helper
from imports.log_helper import LogTypes
import imports.color_enum as color_enum

logger = log_helper.Logger("Main")

with open("config.json", "r") as f:
    config = json.load(f)

class Blocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(config["log_channel_id"])
        self.farm_channel_id = int(config["farm_channel_id"])

    @commands.slash_command(name="farmrequests", description="Frage spezielle Ressourcen an.")
    async def farm_requests(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="Farm Requests",
            description="Hier kannst du spezielle Ressourcen anfragen, die du benötigst.",
            color=color_enum.get_color("info"),
        )
        embed.add_field(
            name="Wie funktioniert das?",
            value=(
                "Unter der Narchict findest du denn Button \"Anfragen\", "
                "Schreibe da alle Infos rein, die wir benötigen."
                " Wir werden uns dann so schnell wie möglich darum kümmern und uns bei dir Melden!"
            ),
            inline=False,
        )
        embed.set_footer(text="Danke, dass du unseren Service nutzt!")

        class RequestView(View):
            def __init__(self, bot, log_channel_id, farm_channel_id):
                super().__init__(timeout=180)
                self.bot = bot
                self.log_channel_id = log_channel_id
                self.farm_channel_id = farm_channel_id

            @discord.ui.button(label="Anfragen", style=discord.ButtonStyle.primary)
            async def request_button(self, button: Button, interaction: discord.Interaction):
                await interaction.response.send_modal(
                    RequestModal(
                        self.bot,
                        interaction.user,
                        self.log_channel_id,
                        self.farm_channel_id,
                    )
                )

        await ctx.respond(embed=embed, view=RequestView(self.bot, self.log_channel_id, self.farm_channel_id), ephemeral=True)


class RequestModal(Modal):
    def __init__(self, bot, user, log_channel_id, farm_channel_id):
        super().__init__(title="Ressourcen Anfrage")
        self.bot = bot
        self.user = user
        self.log_channel_id = log_channel_id
        self.farm_channel_id = farm_channel_id

        self.resource_input = InputText(
            label="Welche Ressourcen benötigst du?",
            style=discord.InputTextStyle.long,
            placeholder="Liste die benötigten Ressourcen auf...",
            required=True,
            max_length=500,
        )

        self.reason_input = InputText(
            label="Warum benötigst du diese Ressourcen?",
            style=discord.InputTextStyle.long,
            placeholder="Erkläre den Grund für deine Anfrage...",
            required=True,
            max_length=500,
        )

        self.add_item(self.resource_input)
        self.add_item(self.reason_input)

    async def callback(self, interaction: discord.Interaction):
        farm_channel = self.bot.get_channel(self.farm_channel_id)

        embed = discord.Embed(
            title="Neue Ressourcen Anfrage",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Benutzer",
            value=f"{interaction.user.mention} ({interaction.user.id})",
            inline=False,
        )
        embed.add_field(
            name="Benötigte Ressourcen",
            value=self.resource_input.value,
            inline=False,
        )
        embed.add_field(
            name="Grund der Anfrage",
            value=self.reason_input.value,
            inline=False,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        if farm_channel:
            await farm_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Deine Anfrage wurde erfolgreich gesendet!",
            ephemeral=True,
        )
# Button to accept the request (With Notify the user that their request was accepted)
#class AcceptView(View):
#    def __init__(self, bot, request_id):
#        super().__init__(timeout=None)
#        self.bot = bot
#        self.request_id = request_id
#
#    @discord.ui.button(label="Anfrage Akzeptieren", style=discord.ButtonStyle.success)
#    async def accept_button(self, button: Button, interaction: discord.Interaction):
#        await interaction.response.send_message(
#            f"✅ Die Anfrage mit der ID {self.request_id} wurde akzeptiert.",
#            ephemeral=True,
#        )
        # Notify the user that their request was accepted
        # This part assumes you have a way to map request_id to user
        # user = get_user_by_request_id(self.request_id)
        # if user:
        #     await user.send(f"Deine Anfrage mit der ID {self.request_id} wurde akzeptiert.")

def setup(bot):
    bot.add_cog(Blocks(bot))