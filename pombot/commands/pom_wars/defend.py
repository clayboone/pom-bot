import random
from datetime import datetime

from discord.ext.commands import Context

import pombot.lib.pom_wars.errors as war_crimes
from pombot.config import Pomwars, Reactions
from pombot.data.pom_wars.actions import Defends
from pombot.lib.errors import DescriptionTooLongError
from pombot.lib.messages import send_embed_message
from pombot.lib.pom_wars.action_chances import is_action_successful
from pombot.lib.pom_wars.dedup_tools import check_user_add_pom, get_average_poms
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType


async def do_defend(ctx: Context, *args):
    """Defend your team."""
    description = " ".join(args)
    timestamp = datetime.now()

    try:
        defender = await check_user_add_pom(ctx, description, timestamp)
    except (war_crimes.UserDoesNotExistError, DescriptionTooLongError):
        return

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.DEFEND,
        "was_successful": False,
        "was_critical":   None,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    if not await is_action_successful(ctx.author, timestamp):
        emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
        await ctx.send(f"<@{ctx.author.id}> defence failed! {emote}")
        await Storage.add_pom_war_action(**action)
        return

    action["was_successful"] = True
    await ctx.message.add_reaction(Reactions.SHIELD)

    defend = Defends.get_random(
        team=action["team"],
        average_daily_actions=await get_average_poms(ctx.author),
    )

    await Storage.add_pom_war_action(**action)

    await send_embed_message(
        None,
        title="You have used Defend against {team}s!".format(
            team=(~get_user_team(ctx.author)).value,
        ),
        description=defend.get_message(defender),
        colour=Pomwars.DEFEND_COLOUR,
        icon_url=None,
        _func=ctx.reply,
    )
