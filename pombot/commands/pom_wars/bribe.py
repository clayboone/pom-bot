from datetime import datetime

from discord.ext.commands import Context

from pombot.data.pom_wars.actions import Bribes
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType


async def do_bribe(ctx: Context):
    """What? I don't take bribes..."""
    bribe = Bribes.get_random()
    timestamp = datetime.now()

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.BRIBE,
        "was_successful": True,
        "was_critical":   None,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    await Storage.add_pom_war_action(**action)
    await ctx.reply(bribe.get_message(ctx.author, ctx.bot))
