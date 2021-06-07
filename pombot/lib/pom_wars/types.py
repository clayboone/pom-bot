from string import Template

from discord.ext.commands import Bot
from discord.user import User as DiscordUser

from pombot.config import Pomwars
from pombot.lib.types import User as BotUser
from pombot.lib.pom_wars.team import get_user_team
from pombot.lib.tiny_tools import normalize_newlines


class Attack:
    """An attack constructable from an actions XML element."""
    def __init__(self, story: str, is_heavy: bool, is_critical: bool):
        self._story = story
        self._is_heavy = is_heavy
        self._is_critical = is_critical

    @property
    def damage(self):
        """Return the total damage this attack produces after heavy- and
        critical- modifiers.
        """
        normal_dmg = Pomwars.BASE_DAMAGE_FOR_NORMAL_ATTACKS
        heavy_dmg = Pomwars.BASE_DAMAGE_FOR_HEAVY_ATTACKS
        base_damage = heavy_dmg if self._is_heavy else normal_dmg

        if self._is_critical:
            return base_damage * Pomwars.DAMAGE_MULTIPLIER_FOR_CRITICAL

        return base_damage

    def get_message(self, adjusted_damage: int = None) -> str:
        """Return the effect and the markdown-formatted story for this attack as
        a combined string.
        """
        dmg = adjusted_damage or self.damage
        dmg_str = f"{dmg:.1f}" if dmg % 1 else str(int(dmg))
        message_lines = [f"** **\n{Pomwars.Emotes.ATTACK} `{dmg_str} damage!`"]

        if self._is_critical:
            message_lines += [f"{Pomwars.Emotes.CRITICAL} `Critical attack!`"]

        action_result = "\n".join(message_lines)
        formatted_story = "*" + normalize_newlines(self._story) + "*"

        return "\n\n".join([action_result, formatted_story])

    def get_title(self, user: DiscordUser) -> str:
        """Title that includes the name of the team user attacked."""
        title = "You have used{indicator}Attack against {team}!".format(
            indicator = " Heavy " if self._is_heavy else " ",
            team=f"{(~get_user_team(user)).value}s",
        )

        return title

    @property
    def colour(self) -> int:
        """Return an embed colour based on whether the attack is heavy."""
        return (Pomwars.HEAVY_ATTACK_COLOUR
                if self._is_heavy else Pomwars.NORMAL_ATTACK_COLOUR)


class Defend:
    """A defend constructable from an actions XML element."""
    def __init__(self, story: str):
        self._story = story

    def get_message(self, user: BotUser) -> str:
        """Return the effect and the markdown-formatted story for this defend
        as a combined string.
        """
        action_result = "** **\n{emt} `{dfn:.0f}% team damage reduction!`".format(
            emt=Pomwars.Emotes.DEFEND,
            dfn=100 * Pomwars.DEFEND_LEVEL_MULTIPLIERS[user.defend_level],
        )
        formatted_story = "*" + normalize_newlines(self._story) + "*"

        return "\n\n".join([action_result, formatted_story])


class Bribe:
    """A bribe constructable from an actions XML element."""
    def __init__(self, story: str):
        self._story = story

    def get_message(self, user: DiscordUser, bot: Bot) -> str:
        """Return the markdown-formatted story for this bribe as a combined
        string.
        """
        story = Template(normalize_newlines(self._story))

        return story.safe_substitute(
            NAME=user.name,
            DISPLAY_NAME=user.display_name,
            DISCRIMINATOR=user.discriminator,
            BOTNAME=bot.user.name
        )
