import unittest
from functools import partial
from unittest.async_case import IsolatedAsyncioTestCase

from discord.ext.commands.core import _CaseInsensitiveDict, GroupMixin
from parameterized import parameterized

import pombot
from pombot.commands.help import OFFSET
from pombot.config import Config, Debug
from pombot.extensions.general import setup as setup_general_commands
from pombot.extensions.pom_wars import setup as setup_pomwars_commands
from tests.helpers import mock_discord

ADMIN_ROLE = "AdminRole"


class TestHelpCommand(IsolatedAsyncioTestCase):
    """Test the !help command."""
    ctx = None

    @classmethod
    def setUpClass(cls):
        Debug.disable()

        cls.__admin_roles_orig = Config.ADMIN_ROLES
        Config.ADMIN_ROLES = [ADMIN_ROLE]

    async def asyncSetUp(self):
        self.ctx = mock_discord.MockContext()
        self.ctx.bot.all_commands = _CaseInsensitiveDict()
        self.ctx.bot.add_command = partial(GroupMixin.add_command, self.ctx.bot)

        setup_general_commands(self.ctx.bot)
        setup_pomwars_commands(self.ctx.bot)

        self.ctx.bot.commands = set(self.ctx.bot.all_commands.values())

    @classmethod
    def tearDownClass(cls):
        Config.ADMIN_ROLES = cls.__admin_roles_orig

    @parameterized.expand([
        (True,),   # Calling user is an admin.
        (False,),  # Calling user is NOT an admin.
    ])
    async def test_user_calling_help_contains_admin_commands_only_with_admin_role(
        self,
        is_user_an_admin,
    ):
        """Test a user typing `!help` only contains admin commands when the user
        has an admin role.
        """
        if is_user_an_admin:
            self.ctx.author = mock_discord.MockMember(
                roles=[mock_discord.MockRole(
                    name=ADMIN_ROLE,
                    position=2,  # Position 1 defaults to `@everyone`.
                )])

        self.ctx.invoked_with = "help"
        await pombot.commands.do_help(self.ctx)
        self.assertEqual(1, len(self.ctx.author.send.call_args_list))

        admin_command_names = {
            cmd.name
            for cmd in [cmd for cmd in self.ctx.bot.commands if cmd.checks]
            for check in cmd.checks if "roles_needed" in check.keywords
            if ADMIN_ROLE in check.keywords["roles_needed"]
        }

        command_names_sent_to_user = {
            line.removeprefix(OFFSET).split(":")[0]
            for line in self.ctx.author.send            \
                                       .call_args       \
                                       .kwargs["embed"] \
                                       .description     \
                                       .splitlines()
            if line.startswith(OFFSET)
        }

        admin_commands_sent_to_user = (admin_cmd in command_names_sent_to_user
                                       for admin_cmd in admin_command_names)

        if is_user_an_admin:
            self.assertTrue(all(admin_commands_sent_to_user))
        else:
            self.assertFalse(any(admin_commands_sent_to_user))


if __name__ == "__main__":
    unittest.main()
