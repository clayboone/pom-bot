from datetime import datetime, timedelta

from discord.ext.commands import Context
from discord.user import User as DiscordUser

import pombot.lib.pom_wars.errors as war_crimes
from pombot.config import Config, Pomwars, Reactions
from pombot.lib.errors import DescriptionTooLongError
from pombot.lib.storage import Storage
from pombot.lib.types import DateRange, User as BotUser


async def check_user_add_pom(
    ctx: Context,
    description: str,
    timestamp: datetime,
) -> BotUser:
    """Based on `ctx` verify a user exists, ensure the pom description is within
    limits and add their pom to the DB.

    @param ctx The context to use for reading author and replying.
    @param description Pom description provided by the user via args.
    @param timestamp The time a user issued the command.
    @raises UserDoesNotExistError, DescriptionTooLongError.
    @return The user from the DB based on their ID.
    """
    try:
        user = await Storage.get_user_by_id(ctx.author.id)
    except war_crimes.UserDoesNotExistError:
        await ctx.reply("How did you get in here? You haven't joined the war!")
        await ctx.message.add_reaction(Reactions.ROBOT)
        raise

    if len(description) > Config.DESCRIPTION_LIMIT:
        await ctx.message.add_reaction(Reactions.WARNING)
        await ctx.send(f"{ctx.author.mention}, your pom description must "
                        f"be fewer than {Config.DESCRIPTION_LIMIT} characters.")
        raise DescriptionTooLongError()

    await Storage.add_poms_to_user_session(
        ctx.author,
        descript=description,
        count=1,
        time_set=timestamp,
    )
    await ctx.message.add_reaction(Reactions.TOMATO)

    return user


async def get_average_poms(user: DiscordUser) -> float:
    today = datetime.today().strftime("%B %d").split()
    last_week = (datetime.today() - timedelta(days=Pomwars.AVERAGING_PERIOD_DAYS)).strftime("%B %d").split()

    actions = await Storage.get_actions(
        user=user,
        was_successful=Pomwars.CONSIDER_ONLY_SUCCESSFUL_ACTIONS,
        date_range=DateRange(*today, *last_week),
    )

    #FIXME don't consider anything except attacks and defends (no bribes).

    if not Pomwars.CONSIDER_ONLY_SUCCESSFUL_ACTIONS:
        #FIXME make shadow cap list comp
        ...

    return 4.2  #FIXME obviously
