import discord, json
from discord.ext import commands
from datetime import datetime

import imports.log_helper as log_helper
from imports.log_helper import LogTypes
import imports.color_enum as colors
import imports.yuuki_helper as yh

logger = log_helper.Logger("Shop-Admin")

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


class ShopAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.log("ShopAdminCog initialized.", LogTypes.SYSTEM)

    # -----------------------------------
    # Slash Command: Update Request
    # -----------------------------------
    @commands.slash_command(
        name="updaterequest",
        description="Aktualisiere eine Anfrage (Admin)"
    )
    @yh.is_staff()
    async def update_request(
        self,
        ctx: discord.ApplicationContext,
        request_id: int,
        field: str = discord.Option(
            description="Welches Feld soll geändert werden?",
            choices=["status", "cost_amount", "assigned_to"]
        ),
        new_value: str = discord.Option(
            description="Neuer Wert für das Feld"
        )
    ):
        cur = self.bot.db.execute(
            "SELECT * FROM requests WHERE request_id = ?",
            (request_id,)
        )
        req = cur.fetchone()

        if not req:
            await ctx.respond(
                embed=self._error_embed("Anfrage nicht gefunden."),
                ephemeral=True
            )
            return

        updates = {field: new_value}

        # Auto completed_at
        if field == "status" and new_value == "done":
            updates["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            for key, value in updates.items():
                self.bot.db.execute(
                    f"UPDATE requests SET {key} = ? WHERE request_id = ?",
                    (value, request_id),
                    commit=True
                )

            # DM an User
            await yh.notify_request_owner(
                self.bot,
                req,
                field,
                new_value
            )

            embed = discord.Embed(
                title="✅ Anfrage aktualisiert",
                color=colors.get_color("success"),
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="Anfrage ID",
                value=f"#{request_id}",
                inline=False
            )

            if field == "status":
                embed.add_field(
                    name="Neuer Status",
                    value=yh.format_status(new_value),
                    inline=False
                )
            elif field == "assigned_to":
                embed.add_field(
                    name="Zugewiesen an",
                    value=f"<@{new_value}>",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Neuer Wert",
                    value=new_value,
                    inline=False
                )

            await ctx.respond(embed=embed)

            logger.log(
                f"Request #{request_id} updated ({updates})",
                LogTypes.SUCCESS
            )

        except Exception as e:
            await ctx.respond(
                embed=self._error_embed(str(e)),
                ephemeral=True
            )
            logger.log(
                f"Error updating request #{request_id}: {e}",
                LogTypes.ERROR
            )

    # -----------------------------------
    # Helper
    # -----------------------------------
    @staticmethod
    def _error_embed(message: str) -> discord.Embed:
        return discord.Embed(
            title="❌ Fehler",
            description=message,
            color=colors.get_color("error")
        )


def setup(bot):
    bot.add_cog(ShopAdminCog(bot))
    logger.log("ShopAdminCog loaded.", LogTypes.SYSTEM)