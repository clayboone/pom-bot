import random
from typing import Callable, Optional

from discord.embeds import Embed
from discord.ext.commands import Context

from pombot.config import Config, Reactions


async def send_embed_message(
        ctx: Optional[Context],
        *,
        title: str,
        description: str,
        colour=Config.EMBED_COLOUR,
        icon_url=Config.EMBED_IMAGE_URL,
        fields: list = None,
        footer: str = None,
        private_message: bool = False,
        _func: Callable = None,
):
    """Send an embedded message using the context."""
    message = Embed(
        description=description,
        colour=colour,
    )
    if icon_url:
        message.set_author(
            name=title,
            icon_url=icon_url,
        )
    else:
        message.title=title
        message.description=description
        message.colour=colour

    if fields:
        for field in fields:
            name, value, inline = field
            message.add_field(name=name, value=value, inline=inline)

    if footer:
        message.set_footer(text=footer)

    if ctx is None:
        coro = _func
    else:
        coro = ctx.author.send if private_message else ctx.send

    # Allow the TypeError to bubble up when both ctx and _func are None.
    return await coro(embed=message)

async def send_permission_denied_msg(ctx: Context):
    """Reply to the user with a random "permission denied" message."""
    message, *_ = random.choices([
        "You do not have access to this command.",
        "Sorry, that command is out-of-order.",
        "!!! ACCESS DENIED !!! \\**whale noises\\**",
        "Wir konnten die Smaragde nicht finden!",
        "Do you smell that?",
        "\\**(Windows XP startup sound)\\**",
        "This is not the command you're looking for. \\**waves hand\\**",
        "*noop*",
        "Command permenently moved to a different folder.",
        "This command is in another castle.",
        "Okay, let me get my tools.. brb",
        "(╯°□°）╯︵ ¡ƃuoɹʍ ʇuǝʍ ƃuıɥʇǝɯoS",
    ])

    await ctx.message.add_reaction(Reactions.ROBOT)
    await ctx.send(message)
