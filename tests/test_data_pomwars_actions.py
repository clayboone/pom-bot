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
        schema = actions.ACTIONS_SCHEMA
        cls.pomwars_actions_dir_orig = Locations.POMWARS_ACTIONS_DIR

        cls.temp_actions_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        Locations.POMWARS_ACTIONS_DIR = Path(cls.temp_actions_dir.name)

        shutil.copy(schema, Locations.POMWARS_ACTIONS_DIR)

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

    def test_actions_get_random(self):
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

    #FIXME need a test to make sure that the right message for the right tier is
    #returned for all tiers.


if __name__ == "__main__":
    unittest.main()
