import textwrap

from discord.ext.commands import Context

from pombot.config import Reactions


async def do_reset(ctx: Context):
    """Deprecated command; see !poms and !bank.

    This command is disabled and will be removed soon. See `!help poms` and
    `!help bank` instead.
    """
    await ctx.reply(textwrap.dedent("""\
        This command has been disabled. See `!help poms` and `!help bank` instead.
    """))
    await ctx.message.add_reaction(Reactions.ROBOT)
