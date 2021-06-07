import logging
from pathlib import Path

THIS_DIR = Path(__file__).parent
POM_WARS_DATA_DIR = THIS_DIR / "pom_wars"

_log = logging.getLogger(__name__)


class Limits:
    """Character limits imposed by the Discord API."""
    MAX_CHARACTERS_PER_MESSAGE = 2000
    MAX_CHARACTERS_PER_EMBED = 6000

    MAX_EMBED_TITLE       = 256
    MAX_EMBED_DESCRIPTION = 2048
    MAX_NUM_EMBED_FIELDS  = 25
    MAX_EMBED_FIELD_NAME  = 256
    MAX_EMBED_FIELD_VALUE = 1024
    MAX_EMBED_FOOTER_TEXT = 2048
    MAX_EMBED_AUTHOR_NAME = 256


class Locations:
    """Path-like locations of data for the bot."""
    DISCLAIMERS = THIS_DIR / "disclaimers.xml"
    POMWARS_ACTIONS_DIR = POM_WARS_DATA_DIR / "actions"
    SCOREBOARD_BODY = POM_WARS_DATA_DIR / "scoreboard.txt"
