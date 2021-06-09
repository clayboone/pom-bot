import shutil
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

from lxml import etree
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

    @parameterized.expand([
        ("normal_attack inside team",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <normal_attack>valid normal attack</normal_attack>
                </team>
            </actions>
        """)),
        ("heavy_attack inside team",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <heavy_attack>valid heavy attack</heavy_attack>
                </team>
            </actions>
        """)),
        ("is_critical is valid attack attribute",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <normal_attack is_critical="true">valid critical normal attack</normal_attack>
                    <normal_attack is_critical="false">valid normal attack</normal_attack>
                    <heavy_attack is_critical="true">valid critical heavy attack</heavy_attack>
                    <heavy_attack is_critical="false">valid heavy attack</heavy_attack>
                </team>
            </actions>
        """)),
        ("defend inside team",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <defend>valid defend</defend>
                </team>
            </actions>
        """)),
        ("bribe inside actions",
         textwrap.dedent("""\
            <actions>
                <bribe>valid bribe</bribe>
            </actions>
        """)),
    ])
    def test_valid_actions_xmls(self, msg, xml):
        """Test various ways of how to write an actions XML."""
        self.write_actions_xml(xml)

        with assert_not_raises(test=self, msg=msg):
            self.instantiate_actions()

    @parameterized.expand([
        ("<normal_attack> must be inside a <team> tag",
         textwrap.dedent("""\
            <actions>
                <normal_attack>invalid attack</normal_attack>
            </actions>
        """)),
        ("<heavy_attack> must be inside a <team> tag",
         textwrap.dedent("""\
            <actions>
                <heavy_attack>invalid attack</heavy_attack>
            </actions>
        """)),
        ("<defend> must be inside a <team> tag",
         textwrap.dedent("""\
            <actions>
                <defend>invalid defend</defend>
            </actions>
        """)),
        ("<defend> attribute is_critical is not allowed",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <defend is_critical="true">invalid defend</defend>
                </team>
            </actions>
        """)),
        ("<bribe> must be inside an <actions> tag",
         textwrap.dedent(f"""\
            <actions>
                <team name="{Pomwars.KNIGHT_ROLE}">
                    <bribe>invalid bribe</bribe>
                </team>
            </actions>
        """)),
        ("team attribute is not allowed",
         textwrap.dedent(f"""\
            <actions>
                <bribe team="{Pomwars.KNIGHT_ROLE}">invalid bribe</bribe>
            </actions>
        """)),
    ])
    def test_invalid_actions_xmls(self, msg, xml):
        """Test various ways of how _not_ to write an actions XML."""
        self.write_actions_xml(xml)

        with self.assertRaises(etree.XMLSyntaxError, msg=msg):  # pylint: disable=c-extension-no-member
            self.instantiate_actions()

    def test_actions_get_random(self):
        """Test actions can be retrieved from correctly formed actions XMLs."""
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
                    <normal_attack is_critical="true">{stories["kn_crit_norm"]}</normal_attack>
                    <heavy_attack is_critical="true">{stories["kn_crit_heav"]}</heavy_attack>
                    <normal_attack>{stories["kn_norm"]}</normal_attack>
                    <heavy_attack>{stories["kn_heav"]}</heavy_attack>
                    <defend>{stories["kn_def"]}</defend>
                </team>
                <team name="{Pomwars.VIKING_ROLE}">
                    <normal_attack is_critical="true">{stories["vk_crit_norm"]}</normal_attack>
                    <heavy_attack is_critical="true">{stories["vk_crit_heav"]}</heavy_attack>
                    <normal_attack>{stories["vk_norm"]}</normal_attack>
                    <heavy_attack>{stories["vk_heav"]}</heavy_attack>
                    <defend>{stories["vk_def"]}</defend>
                </team>
                <bribe>{stories["br"]}</bribe>
            </actions>
        """))

        with assert_not_raises():
            attacks, defends, bribes = self.instantiate_actions()

        for action, kwargs, expected_story in (
            # pylint: disable=line-too-long
            (attacks, {"team": Team.KNIGHTS, "critical": False, "heavy": False}, stories["kn_norm"]),
            (attacks, {"team": Team.KNIGHTS, "critical": False, "heavy": True},  stories["kn_heav"]),
            (attacks, {"team": Team.KNIGHTS, "critical": True,  "heavy": False}, stories["kn_crit_norm"]),
            (attacks, {"team": Team.KNIGHTS, "critical": True,  "heavy": True},  stories["kn_crit_heav"]),
            (attacks, {"team": Team.VIKINGS, "critical": False, "heavy": False}, stories["vk_norm"]),
            (attacks, {"team": Team.VIKINGS, "critical": False, "heavy": True},  stories["vk_heav"]),
            (attacks, {"team": Team.VIKINGS, "critical": True,  "heavy": False}, stories["vk_crit_norm"]),
            (attacks, {"team": Team.VIKINGS, "critical": True,  "heavy": True},  stories["vk_crit_heav"]),
            (defends, {"team": Team.KNIGHTS}, stories["kn_def"]),
            (defends, {"team": Team.VIKINGS}, stories["vk_def"]),
            (bribes,  {}, stories["br"])
            # pylint: enable=line-too-long
        ):
            actual_story = action.get_random(**kwargs)._story
            self.assertEqual(expected_story, actual_story)


if __name__ == "__main__":
    unittest.main()
