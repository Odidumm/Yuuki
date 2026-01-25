import json
from typing import Optional
from datetime import datetime
from discord.ext import commands
import discord

import imports.log_helper as log_helper
from imports.log_helper import LogTypes
import imports.database as db

logger = log_helper.Logger("Yuuki-Helper")

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

STATUS_MAPPING = config.get("status_mapping", {})


# -------------------------------
# Checks
# -------------------------------
def is_staff():
    async def predicate(ctx):
        staff_roles = [int(r) for r in config["staff_role_ids"]]
        return any(role.id in staff_roles for role in ctx.author.roles)
    return commands.check(predicate)


# -------------------------------
# Formatter
# -------------------------------
def format_status(status: str) -> str:
    return STATUS_MAPPING.get(status, status)


def format_datetime(value: Optional[str]) -> str:
    if not value:
        return "—"
    return datetime.strptime(
        value, "%Y-%m-%d %H:%M:%S"
    ).strftime("%d.%m.%Y %H:%M")


async def format_assigned_to(bot, value: Optional[str]) -> str:
    if not value:
        return "Nicht zugewiesen"
    try:
        user = await bot.fetch_user(int(value))
        return user.mention
    except Exception:
        return value


# -------------------------------
# DM Notification
# -------------------------------
async def notify_request_owner(
    bot,
    request_row,
    field: str,
    new_value: str
):
    try:
        user = await bot.fetch_user(int(request_row["user_id"]))

        embed = discord.Embed(
            title="🔔 Deine Anfrage wurde aktualisiert",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Anfrage ID",
            value=f"#{request_row['request_id']}",
            inline=False
        )

        if field == "status":
            embed.add_field(
                name="Neuer Status",
                value=format_status(new_value),
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
                name=f"Neuer Wert ({field})",
                value=new_value,
                inline=False
            )

        await user.send(embed=embed)

    except Exception as e:
        logger.log(
            f"Failed to DM user {request_row['user_id']}: {e}",
            LogTypes.WARNING
        )