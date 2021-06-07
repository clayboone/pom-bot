import random
from enum import Enum
from typing import Union

from lxml import etree

from pombot.data import Locations
from pombot.lib.pom_wars.team import Team
from pombot.lib.pom_wars.types import Attack, Bribe, Defend
from pombot.lib.tiny_tools import str2bool, flatten

ACTIONS_SCHEMA = Locations.POMWARS_ACTIONS_DIR / "actions.xsd"


class _XMLTags(str, Enum):
    NORMAL_ATTACK = "normal_attack"
    HEAVY_ATTACK = "heavy_attack"
    DEFEND = "defend"
    BRIBE = "bribe"


class _XMLLoader:
    def __init__(self) -> None:
        # pylint: disable=c-extension-no-member
        schema = etree.XMLSchema(etree.parse(str(ACTIONS_SCHEMA)))
        parser = etree.XMLParser(schema=schema)

        self._xmls = [
            etree.parse(str(path), parser=parser).getroot()
            for path in Locations.POMWARS_ACTIONS_DIR.rglob("*.xml")
        ]
        # pylint: enable=c-extension-no-member


class _Attacks(_XMLLoader):
    def get_random(self, *, team: Union[str, Team], critical: bool, heavy: bool) -> Attack:
        """Return a random Attack from the XMLs."""
        tags = {False: _XMLTags.NORMAL_ATTACK, True: _XMLTags.HEAVY_ATTACK}
        choice = random.choice([
            e for e in flatten(
                x.xpath(f".//team[@name='{team}']/{tags[heavy]}")
                for x in self._xmls)
            if str2bool(e.attrib.get("is_critical", "false")) == critical
        ])

        return Attack(
            story=choice.text.strip(),
            is_heavy=heavy,
            is_critical=critical,
        )


class _Defends(_XMLLoader):
    def get_random(self, team: Union[str, Team]):
        """Return a random Defend from the XMLs."""
        choice = random.choice(
            flatten(
                x.xpath(f".//team[@name='{team}']/{_XMLTags.DEFEND}")
                for x in self._xmls))

        return Defend(story=choice.text.strip())


class _Bribes(_XMLLoader):
    def get_random(self):
        """Return a random Bribe from the XMLs."""
        choice = random.choice(
            flatten(x.xpath(f".//{_XMLTags.BRIBE}") for x in self._xmls))

        return Bribe(story=choice.text.strip())


# Exports
Attacks = _Attacks()
Defends = _Defends()
Bribes = _Bribes()
