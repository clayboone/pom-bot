import inspect
import re
import textwrap
from collections import Counter
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, List

import discord
from discord.ext.commands import Command, Context
from discord.ext.commands.errors import MissingAnyRole, NoPrivateMessage

from pombot.lib.types import DateRange


def positive_int(value: Any) -> int:
    """Return the provided value if it is a positive whole number. Raise
    ValueError otherwise.
    """
    if (intval := int(value)) < 0:
        raise ValueError(f"Expected a positive integer, got {value}")

    return intval


def str2bool(value: str) -> bool:
    """Coerce a string to a bool based on its value."""
    return value.casefold() in {"yes", "y", "1", "true", "t"}


def daterange_from_timestamp(timestamp: datetime):
    """Get the DateRange of the day containing the given timestamp."""
    get_timestamp_at_time = lambda time: datetime.strptime(
        datetime.strftime(timestamp, f"%Y-%m-%d {time}"), "%Y-%m-%d %H:%M:%S")

    morning = get_timestamp_at_time("00:00:00")
    evening = get_timestamp_at_time("23:59:59")

    return DateRange(morning, evening)


def has_any_role(ctx: Context, roles_needed=None):
    """A non-decorator reimplementation of discord.ext.commands.has_any_role,
    but with dignity.

    @raises dicord.ext.commands.errors.CheckFailure.
    """
    roles_needed = roles_needed or []

    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        raise NoPrivateMessage()

    get_user_roles = partial(discord.utils.get, ctx.author.roles)

    if not any(get_user_roles(id=role_needed) is not None
            if isinstance(role_needed, int)
            else get_user_roles(name=role_needed) is not None
                for role_needed in roles_needed):
        raise MissingAnyRole(roles_needed)


class BotCommand(Command):
    """Wrapper around discord.ext.commands.Command which ensures that the
    passed function is a coroutine and maps the caller's module __name__ to
    the `extension` attribute.
    """
    def __init__(self, func, **kwargs):
        # The exception raised by `discord` is not helpful in finding the
        # actual problem, so append the real issue to the traceback.
        assert inspect.iscoroutinefunction(func), \
            f"Function {func.__name__} is not a coroutine"

        self.duplicate_aliases = []
        if aliases := kwargs.get("aliases"):
            unique_commands = set(aliases)
            repeated_commands = set(Counter(aliases) - Counter(unique_commands))

            kwargs["aliases"] = sorted(unique_commands - repeated_commands)
            self.duplicate_aliases = sorted(repeated_commands)

        super().__init__(func, **kwargs)
        self.extension = Path(inspect.stack()[1].filename).stem


def normalize_newlines(text: str) -> str:
    r"""Replace newlines with spaces, unless the newline is followed by
    another newline.

    This allows us to write text in a nice format in editors (help text,
    action stories, etc.) but still display them correctly in messages. For
    example:

    >>> import textwrap
    >>> text_in_file = textwrap.dedent("\
    ...     This is an example.
    ...     This line and the last line will be joined by a space.
    ...
    ...     This line will be another paragraph in the message.
    ... ")
    >>> message_to_send = normalize_newlines(text_in_file)

    As an attempt to give developers a means of forcing single-spaced lines,
    any carriage return ("\r") will be replaced with newlines after the
    initial normalization.
    """
    normalized = re.sub(r"(?<!\n)\n(?!\n)|\n{3,}", " ", text).strip()
    return normalized.replace("\r", "\n")


def normalize_and_dedent(text: str) -> str:
    """Same as normalize_newlines, but un-indent the text first."""
    return normalize_newlines(textwrap.dedent(text))


class classproperty(property):  # pylint: disable=invalid-name
    """Decorator to use classmethods as properties."""
    def __get__(self, obj, objtype=None):
        return super().__get__(objtype)

    def __set__(self, obj, value):
        raise RuntimeError("Cannot set classproperty")

    def __delete__(self, obj):
        raise RuntimeError("Cannot delete classproperty")


def explode_after_char(word: str, char: str) -> List[str]:
    """Explode the string after the first occurence of a `char`.

    This will take a string like "hello.world" and return a list of strings
    in this pattern:
    ['hello.w',
     'hello.wo',
     'hello.wor',
     'hello.worl',
     'hello.world']

    Raises:
        ValueError when the specified `char` is not found in `word` before
        the last character (ie. when `word` ends with a `char`).
    """
    pos = word[:-1].index(char)
    return [word[0:pos+2+i] for i in range(len(word) - (pos+1))]


class PolyStr(str):
    """Subclass of str which adds custom methods."""
    def format(self, *args, **kwargs):
        return self.__class__(super().format(*args, **kwargs))

    def replace_final_occurence(self, old: str, new: str):
        """Like `replace`, but only replace the last occurence of `old`."""
        if (index := self.rfind(old)) > 0:
            return self.__class__(" ".join((self[:index], new, self[index + len(old):])))

        return self


def flatten(list_of_lists: list) -> list:
    """Convert a list of lists into a simple list.

    This has the effect of removing empty lists as well.
    """
    return [item for sublist in list_of_lists for item in sublist]
