import shutil
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

from parameterized import parameterized

from pombot.config import Pomwars
from pombot.data import Locations
from pombot.data.pom_wars import actions
from pombot.lib.pom_wars.team import Team
from tests.helpers.semantics import assert_not_raises

# pylint: disable=protected-access


class TestActionsData(unittest.TestCase):
    """Test reading the various action descriptions from XML."""
    @classmethod
    def setUpClass(cls):
        cls.pomwars_actions_dir_orig = Locations.POMWARS_ACTIONS_DIR

        cls.temp_actions_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        Locations.POMWARS_ACTIONS_DIR = Path(cls.temp_actions_dir.name)

        shutil.copy(actions.ACTIONS_SCHEMA, Locations.POMWARS_ACTIONS_DIR)

    def setUp(self):
        # Invalid XMLs will cause valid XML tests to fail.
        for item in Locations.POMWARS_ACTIONS_DIR.rglob("*.xml"):
            item.unlink()

    @classmethod
    def tearDownClass(cls):
        cls.temp_actions_dir.cleanup()
        Locations.POMWARS_ACTIONS_DIR = cls.pomwars_actions_dir_orig

    @staticmethod
    def write_actions_xml(xml_content: str, filename: str = "actions.xml"):
        """Write xml_content to an XML file in the actions directory."""
        xml_path = Locations.POMWARS_ACTIONS_DIR / filename
        xml_path.write_text(xml_content)

    @staticmethod
    def instantiate_actions() -> Tuple:
        """Create new instances of the protected actions generators."""
        return actions._Attacks(), actions._Defends(), actions._Bribes()

    def test_actions_get_random_story_from_correct_node(self):
        """Test actions can be retrieved from correctly formed actions XMLs."""
        average_daily_actions = 1

        stories = {
            "kn_crit_norm": "knight critical normal attack",
            "kn_crit_heav": "knight critical heavy attack",
            "kn_norm":      "knight normal attack",
            "kn_heav":      "knight heavy attack",
            "kn_def":       "knight defend",
            "vk_crit_norm": "viking critical normal attack",
            "vk_crit_heav": "viking critical heavy attack",
            "vk_norm":      "viking normal attack",
            "vk_heav":      "viking heavy attack",
            "vk_def":       "viking defend",
            "br":           "bribe",
        }

        self.write_actions_xml(textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <tier level="{average_daily_actions}">
                        <normal_attack critical="true">{stories["kn_crit_norm"]}</normal_attack>
                        <heavy_attack critical="true">{stories["kn_crit_heav"]}</heavy_attack>
                        <normal_attack>{stories["kn_norm"]}</normal_attack>
                        <heavy_attack>{stories["kn_heav"]}</heavy_attack>
                        <defend>{stories["kn_def"]}</defend>
                    </tier>
                </team>
                <team name="{Pomwars.VIKING_ROLE}">
                    <tier level="{average_daily_actions}">
                        <normal_attack critical="true">{stories["vk_crit_norm"]}</normal_attack>
                        <heavy_attack critical="true">{stories["vk_crit_heav"]}</heavy_attack>
                        <normal_attack>{stories["vk_norm"]}</normal_attack>
                        <heavy_attack>{stories["vk_heav"]}</heavy_attack>
                        <defend>{stories["vk_def"]}</defend>
                    </tier>
                </team>
                <bribe>{stories["br"]}</bribe>
            </actions>
        """))

        with assert_not_raises():
            attacks, defends, bribes = self.instantiate_actions()

        for action, kwargs, expected_story in (
            # pylint: disable=line-too-long
            (attacks, {"team": Team.KNIGHTS, "average_daily_actions": average_daily_actions, "critical": False, "heavy": False}, stories["kn_norm"]),
            (attacks, {"team": Team.KNIGHTS, "average_daily_actions": average_daily_actions, "critical": False, "heavy": True},  stories["kn_heav"]),
            (attacks, {"team": Team.KNIGHTS, "average_daily_actions": average_daily_actions, "critical": True,  "heavy": False}, stories["kn_crit_norm"]),
            (attacks, {"team": Team.KNIGHTS, "average_daily_actions": average_daily_actions, "critical": True,  "heavy": True},  stories["kn_crit_heav"]),
            (attacks, {"team": Team.VIKINGS, "average_daily_actions": average_daily_actions, "critical": False, "heavy": False}, stories["vk_norm"]),
            (attacks, {"team": Team.VIKINGS, "average_daily_actions": average_daily_actions, "critical": False, "heavy": True},  stories["vk_heav"]),
            (attacks, {"team": Team.VIKINGS, "average_daily_actions": average_daily_actions, "critical": True,  "heavy": False}, stories["vk_crit_norm"]),
            (attacks, {"team": Team.VIKINGS, "average_daily_actions": average_daily_actions, "critical": True,  "heavy": True},  stories["vk_crit_heav"]),

            (defends, {"team": Team.KNIGHTS, "average_daily_actions": average_daily_actions}, stories["kn_def"]),
            (defends, {"team": Team.VIKINGS, "average_daily_actions": average_daily_actions}, stories["vk_def"]),

            (bribes,  {}, stories["br"])
            # pylint: enable=line-too-long
        ):
            actual_story = action.get_random(**kwargs)._story
            self.assertEqual(expected_story, actual_story)

    @parameterized.expand([
        # You're in tier 1.
        (0,  1),
        (1,  1),
        (2,  1),
        (3,  1),
                    # You're in tier 2.
                    (4,  2),
                    (5,  2),
                    (6,  2),
                    (7,  2),
                                # You're in tier 3.
                                (8,  3),
                                (9,  3),
                                (10, 3),
                                (11, 3),
                                (12, 3),
                                # ...
    ])
    def test_actions_get_random_story_from_correct_tier(
        self,
        average_daily_actions,
        expected_tier,
    ):
        """Test actions are retrieved from the correct tier in the actions XMLs
        given a player's average number of daily actions.
        """
        team_name = Pomwars.KNIGHT_ROLE

        stories = {
            1: {
                "nrm": "tier 1 normal attack",
                "hvy": "tier 1 heavy attack",
                "dfn": "tier 1 defend",
            },
            2: {
                "nrm": "tier 2 normal attack",
                "hvy": "tier 2 heavy attack",
                "dfn": "tier 2 defend",
            },
            3: {
                "nrm": "tier 3 normal attack",
                "hvy": "tier 3 heavy attack",
                "dfn": "tier 3 defend",
            },
        }

        tiers = "".join([f"""\
            <tier level="{tier}">
                <normal_attack>{stories[tier]["nrm"]}</normal_attack>
                <heavy_attack>{stories[tier]["hvy"]}</heavy_attack>
                <defend>{stories[tier]["dfn"]}</defend>
            </tier>
        """ for tier in stories])

        self.write_actions_xml(textwrap.dedent(f"""\
            <actions>
                <team name="{team_name}">
                    {tiers}
                </team>
            </actions>
        """))

        with assert_not_raises():
            attacks, defends, _ = self.instantiate_actions()

        average = {"average_daily_actions": average_daily_actions}

        actual_nrm_story = attacks.get_random(team=team_name,
                                              critical=False,
                                              heavy=False,
                                              **average)._story

        actual_hvy_story = attacks.get_random(team=team_name,
                                              critical=False,
                                              heavy=True,
                                              **average)._story

        actual_dfn_story = defends.get_random(team=team_name, **average)._story

        self.assertEqual(stories[expected_tier]["nrm"], actual_nrm_story)
        self.assertEqual(stories[expected_tier]["hvy"], actual_hvy_story)
        self.assertEqual(stories[expected_tier]["dfn"], actual_dfn_story)


if __name__ == "__main__":
    unittest.main()
