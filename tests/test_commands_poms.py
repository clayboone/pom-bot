import random
import re
import string
import unittest
from unittest.async_case import IsolatedAsyncioTestCase

from discord.embeds import Embed
from parameterized import parameterized

import pombot
from pombot.config import Config, Debug
from pombot.data import Limits
from pombot.lib.storage import Storage
from pombot.lib.types import SessionType
from tests.helpers.mock_discord import MockContext
from tests.helpers.semantics import assert_not_raises


class TestPomsCommand(IsolatedAsyncioTestCase):
    """Test the !poms command."""
    ctx = None

    async def asyncSetUp(self) -> None:
        """Ensure database tables exist and create contexts for the tests."""
        Debug.disable()
        self.ctx = MockContext()
        await Storage.create_tables_if_not_exists()
        await Storage.delete_all_rows_from_all_tables()

    async def asyncTearDown(self) -> None:
        """Cleanup the database."""
        await Storage.delete_all_rows_from_all_tables()

    @parameterized.expand(["!poms", "!poms.show"])
    async def test_poms_command_with_no_args(self, invoked_with: str):
        """Test the user typing `!poms` and `!poms.show` with an empty
        session and bank.
        """
        self.ctx.invoked_with = invoked_with.removeprefix("!")
        await pombot.commands.do_poms(self.ctx)

        if response_is_public := self.ctx.invoked_with in Config.PUBLIC_POMS_ALIASES:
            self.assertEqual(1, self.ctx.message.reply.call_count)
            embed_sent_to_user = self.ctx.message.reply.call_args.kwargs["embed"]
        else:
            self.assertEqual(1, self.ctx.author.send.call_count)
            embed_sent_to_user = self.ctx.author.send.call_args.kwargs["embed"]

        if response_is_public:
            self.assertEqual(Embed.Empty, embed_sent_to_user.description)

            expected_fields_sent_to_user = [
                {
                    "name": "**Current Session**",
                    "value": "Start your session by doing\nyour first !pom.\n",
                    "inline": True,
                },
            ]
        else:
            self.assertIn("Session not yet started.", embed_sent_to_user.description)

            expected_fields_sent_to_user = [
                {
                    "name": "**Banked Poms**",
                    "value": "Bank the poms in your current\nsession to add them here!\n",
                    "inline": True,
                },
                {
                    "name": "\u200b",  # Zero-width space.
                    "value": "\u200b",  # Zero-width space.
                    "inline": True,
                },
                {
                    "name": "**Current Session**",
                    "value": "Start your session by doing\nyour first !pom.\n",
                    "inline": True,
                },
            ]

        self.assertEqual(len(expected_fields_sent_to_user),
                         len(embed_sent_to_user.fields))

        for expected, actual in zip(expected_fields_sent_to_user,
                                    embed_sent_to_user.fields):
            self.assertEqual(expected["name"], actual.name)
            self.assertEqual(expected["value"], actual.value)
            self.assertEqual(expected["inline"], actual.inline)

    async def test_too_many_pom_descripts_causes_detailed_direct_message(self):
        """Test the user typing `!poms` when the response of the message
        would exceed Discord limits.
        """
        # Deterministically generate pom descriptions.
        random.seed(42)

        # Make our combined pom descriptions over 6,000 characters.
        descripts = [
            "".join(
                random.choice(string.ascii_letters + string.digits)
                for _ in range(30)) for _ in range(201)
        ]
        await Storage.add_poms_to_user_session(self.ctx.author, descripts, 1)

        # Have at least one "Undesignated" pom.
        await Storage.add_poms_to_user_session(self.ctx.author, None, 1)

        # The command succeeds.
        await self._do_poms_and_verify_response("poms", descripts)

        # Bank our poms.
        await Storage.bank_user_session_poms(self.ctx.author)

        # The command succeeds again.
        await self._do_poms_and_verify_response("bank", descripts)

    async def _do_poms_and_verify_response(
        self,
        expected_response_failed_cmd,
        expected_descripts,
    ):
        self.ctx.send.reset_mock()
        self.ctx.reply.reset_mock()
        self.ctx.author.send.reset_mock()

        with assert_not_raises():
            self.ctx.invoked_with = "poms"
            await pombot.commands.do_poms(self.ctx)

        # The user was DM'd and only DM'd.
        self.assertTrue(self.ctx.author.send.called)
        self.assertFalse(any((self.ctx.send.called, self.ctx.reply.called)))

        first, second, third, *remainder = self.ctx.author.send.call_args_list

        # The first call was the one that raised the error.
        self.assertGreater(len(first.kwargs["embed"]),
                           Limits.MAX_CHARACTERS_PER_EMBED)

        # The second call was as much of the embed that sent successfully.
        self.assertIsNotNone(second.kwargs.get("embed"))

        # The third call was a detailed message of the problem.
        expected_message_response_re = (
            r"```fix\n"
            r"\n"
            r"The combined length of all the pom descriptions in your "
            r"(current session|banked poms) is longer than the maximum embed "
            r"message field size for Discord embeds \([0-9]{4,}, Max is "
            r"([0-9]+)\)\. Please rename a few with \!(poms|bank)\.rename "
            r"\(see \!help (poms|bank)\)\.```"
        )

        self.assertIsNotNone(
            match := re.search(expected_message_response_re, third.args[0]))
        session_type, limit, *cmds = match.groups()

        self.assertTrue(
            (SessionType(session_type.title()) == SessionType.CURRENT
             if expected_response_failed_cmd == "poms" else SessionType(
                 session_type.title()) == SessionType.BANKED))

        self.assertEqual(str(Limits.MAX_EMBED_FIELD_VALUE), limit)
        self.assertTrue(all(cmd == expected_response_failed_cmd for cmd in cmds))

        # The remaining calls detail all of the user's descripts in the session.
        actual_combined_response = "\n".join([
            "\n".join(args) for args in [call.args for call in remainder]
        ])

        for expected_descript in expected_descripts:
            self.assertIn(expected_descript, actual_combined_response)


if __name__ == "__main__":
    unittest.main()
