import discord, json
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from typing import Optional

import imports.log_helper as log_helper
from imports.log_helper import LogTypes
import imports.color_enum as colors

import imports.yuuki_helper as yh

intents = discord.Intents.all()
logger = log_helper.Logger("Shop")

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.log("ShopCog initialized.", LogTypes.SYSTEM)
        self.log_channel_id = int(config["log_channel_id"])
        self.farm_channel_id = int(config["farm_channel_id"])

    @commands.slash_command(name="farmrequests", description="Frage spezielle Ressourcen an.")
    async def farm_requests(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="Farm Requests",
            description="Hier kannst du spezielle Ressourcen anfragen, die du benötigst.",
            color=colors.get_color("info"),
        )
        embed.add_field(
            name="Wie funktioniert das?",
            value=(
                "Unter der Nachricht findest du den Button \"Anfragen\". "
                "Schreibe dort alle Infos rein, die wir benötigen. "
                "Wir melden uns so schnell wie möglich!"
            ),
            inline=False,
        )
        embed.set_footer(text="Danke, dass du unseren Service nutzt!")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

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

        await ctx.respond(
            embed=embed,
            view=RequestView(self.bot, self.log_channel_id, self.farm_channel_id),
            ephemeral=True
        )

    # -----------------------------------
    # Eigene Anfragen anzeigen
    # -----------------------------------
    myrequests = SlashCommandGroup(
        "myrequests",
        "Zeige deine Anfragen"
    )

    @myrequests.command(name="alle", description="Zeige alle deine Anfragen")
    async def myrequests_all(self, ctx: discord.ApplicationContext):
        cur = self.bot.db.execute(
            "SELECT request_id, status, created_at FROM requests WHERE user_id = ?",
            (str(ctx.author.id),)
        )
        requests = cur.fetchall()

        if not requests:
            await ctx.respond("Du hast keine Anfragen.", ephemeral=True)
            return

        embed = discord.Embed(title="Deine Anfragen", color=colors.get_color("info"))

        for req in requests:
            embed.add_field(
                name=f"Anfrage #{req['request_id']}",
                value=f"**Status**: {yh.format_status(req['status'])}\n**Erstellt am**: {yh.format_datetime(req['created_at'])}",
                inline=False
            )

        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed, ephemeral=True)

    @myrequests.command(name="id", description="Zeige eine bestimmte Anfrage")
    async def myrequests_id(
        self,
        ctx: discord.ApplicationContext,
        request_id: int
    ):
        cur = self.bot.db.execute(
            "SELECT * FROM requests WHERE request_id = ? AND user_id = ?",
            (request_id, str(ctx.author.id))
        )
        req = cur.fetchone()

        if not req:
            await ctx.respond(f"Keine Anfrage mit ID #{request_id} gefunden.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Details zu Anfrage #{req['request_id']}",
            color=colors.get_color("info")
        )
        embed.add_field(name="**Status**", value=yh.format_status(req["status"]), inline=False)
        embed.add_field(name="**Erstellt am**", value=yh.format_datetime(req["created_at"]), inline=False)
        embed.add_field(name="**Kosten**", value=req["cost_amount"], inline=False)
        assigned_to_id = req["assigned_to"]

        if assigned_to_id:
            try:
                user = await self.bot.fetch_user(int(assigned_to_id))
                assigned_to_display = user.mention
            except Exception:
                assigned_to_display = f"<@{assigned_to_id}>"
        else:
            assigned_to_display = "Nicht zugewiesen"

        embed.add_field(
            name="Zugewiesen an",
            value=assigned_to_display,
            inline=False
        )

        embed.add_field(
            name="**Abgeschlossen am**",
            value=yh.format_datetime(req["completed_at"]) or "Nicht abgeschlossen",
            inline=False
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="itemstock", description="Teile uns mit, welches Item nicht auf Lager ist.")
    async def item_stock(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="Item Stock Meldung",
            description=(
                "Bitte teile uns mit, welches Item nicht auf Lager ist, "
                "damit wir es so schnell wie möglich nachbestellen können."
            ),
            color=colors.get_color("info"),
        )
        embed.set_footer(text="Danke für deine Mithilfe!")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        class ItemStockView(View):
            def __init__(self, bot, log_channel_id, item_stock_channel_id):
                super().__init__(timeout=180)
                self.bot = bot
                self.log_channel_id = log_channel_id
                self.item_stock_channel_id = item_stock_channel_id

            @discord.ui.button(label="Melden", style=discord.ButtonStyle.primary)
            async def item_stock_button(self, button: Button, interaction: discord.Interaction):
                await interaction.response.send_modal(
                    ItemStockModal(
                        self.bot,
                        interaction.user,
                        self.log_channel_id,
                        self.item_stock_channel_id,
                    )
                )
        await ctx.respond(embed=embed, view=ItemStockView(self.bot, self.log_channel_id, int(config["item_stock_channel_id"])), ephemeral=True)

def setup(bot):
    bot.add_cog(ShopCog(bot))
    logger.log("ShopCog cog loaded.", LogTypes.SYSTEM)

# -----------------------------------
# Modal
# -----------------------------------
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

        self.add_item(self.resource_input)

    async def callback(self, interaction: discord.Interaction):
        farm_channel = self.bot.get_channel(self.farm_channel_id)

        request_id = self.bot.db.create_request(
            str(interaction.user.id),
            self.resource_input.value
        )

        embed = discord.Embed(
            title="Neue Ressourcen Anfrage",
            color=colors.get_color("info"),
            timestamp=discord.utils.utcnow()
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
            name="ID",
            value=f"#{request_id}",
            inline=False,
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Bitte bearbeite diese Anfrage so schnell wie möglich.")

        await farm_channel.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Deine Anfrage wurde erstellt! (ID: #{request_id})",
            ephemeral=True,
        )

class ItemStockModal(Modal):
    def __init__(self, bot, user, log_channel_id, item_stock_channel_id):
        super().__init__(title="Item Stock Meldung")
        self.bot = bot
        self.user = user
        self.log_channel_id = log_channel_id
        self.item_stock_channel_id = item_stock_channel_id

        self.item_input = InputText(
            label="Welches Item ist nicht auf Lager?",
            style=discord.InputTextStyle.short,
            placeholder="Gib den Namen oder die ID des Items ein...",
            required=True,
            max_length=100,
        )

        self.add_item(self.item_input)

    async def callback(self, interaction: discord.Interaction):
        item_stock_channel = self.bot.get_channel(self.item_stock_channel_id)

        embed = discord.Embed(
            title="Item Stock Meldung",
            color=colors.get_color("info"),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Benutzer",
            value=f"{interaction.user.mention} ({interaction.user.id})",
            inline=False,
        )
        embed.add_field(
            name="Nicht auf Lager",
            value=self.item_input.value,
            inline=False,
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Bitte überprüfe den Lagerbestand dieses Items.")

        await item_stock_channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ Deine Meldung wurde gesendet! Wir werden den Lagerbestand überprüfen.",
            ephemeral=True,
        )