import random
from datetime import datetime, timedelta

from discord.ext.commands import Context

import pombot.lib.pom_wars.errors as war_crimes
from pombot.config import Debug, Pomwars, Reactions
from pombot.data.pom_wars.actions import Attacks
from pombot.lib.errors import DescriptionTooLongError
from pombot.lib.messages import send_embed_message
from pombot.lib.pom_wars.action_chances import is_action_successful
from pombot.lib.pom_wars.dedup_tools import check_user_add_pom
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.storage import Storage
from pombot.lib.types import ActionType, DateRange
from pombot.state import State


async def _get_defensive_multiplier(team: str, timestamp: datetime) -> float:
    defend_actions = await Storage.get_actions(
        action_type=ActionType.DEFEND,
        team=team,
        was_successful=True,
        date_range=DateRange(
            timestamp - timedelta(minutes=Pomwars.DEFEND_DURATION_MINUTES),
            timestamp,
        ),
    )
    defenders = await Storage.get_users_by_id([a.user_id for a in defend_actions])
    multipliers = [Pomwars.DEFEND_LEVEL_MULTIPLIERS[d.defend_level] for d in defenders]
    multiplier = min([sum(multipliers), Pomwars.MAXIMUM_TEAM_DEFENCE])

    return 1 - multiplier


async def do_attack(ctx: Context, *args):
    """Attack the other team."""
    timestamp = datetime.now()
    heavy_attack = bool(args) and args[0].casefold() in Pomwars.HEAVY_QUALIFIERS
    description = " ".join(args[1:] if heavy_attack else args)

    try:
        _ = await check_user_add_pom(ctx, description, timestamp)
    except (war_crimes.UserDoesNotExistError, DescriptionTooLongError):
        return

    action = {
        "user":           ctx.author,
        "team":           get_user_team(ctx.author).value,
        "action_type":    ActionType.HEAVY_ATTACK
                              if heavy_attack else ActionType.NORMAL_ATTACK,
        "was_successful": False,
        "was_critical":   False,
        "items_dropped":  "",
        "damage":         None,
        "time_set":       timestamp,
    }

    if not await is_action_successful(ctx.author, timestamp, heavy_attack):
        emote = random.choice(["¯\\_(ツ)_/¯", "(╯°□°）╯︵ ┻━┻"])
        await Storage.add_pom_war_action(**action)
        await ctx.send(f"<@{ctx.author.id}>'s attack missed! {emote}")
        return

    action["was_successful"] = True
    action["was_critical"] = random.random() <= Pomwars.BASE_CHANCE_FOR_CRITICAL
    await ctx.message.add_reaction(Reactions.BOOM)

    attack = Attacks.get_random(
        team=action["team"],
        critical=action["was_critical"],
        heavy=heavy_attack,
    )

    defensive_multiplier = await _get_defensive_multiplier(
        team=(~get_user_team(ctx.author)).value,
        timestamp=timestamp)

    action["damage"] = attack.damage * defensive_multiplier
    await Storage.add_pom_war_action(**action)

    await send_embed_message(
        None,
        title=attack.get_title(ctx.author),
        description=attack.get_message(action["damage"]),
        icon_url=None,
        colour=attack.colour,
        _func=ctx.reply,
    )

    await State.scoreboard.update()

    if Debug.BENCHMARK_POMWAR_ATTACK:
        print(f"!attack took: {datetime.now() - timestamp}")
