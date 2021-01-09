import logging
from contextlib import contextmanager
from datetime import datetime as dt
from datetime import time, timezone
from typing import List, Optional, Set, Tuple

import mysql.connector
from discord.user import User as DiscordUser

import pombot.errors
from pombot.config import Config, Secrets
from pombot.lib.types import Action, ActionType, DateRange, Event, Pom, Team
from pombot.lib.types import User as PombotUser

_log = logging.getLogger(__name__)


@contextmanager
def _mysql_database_cursor():
    db_config = {
        "host": Secrets.MYSQL_HOST,
        "user": Secrets.MYSQL_USER,
        "password": Secrets.MYSQL_PASSWORD,
        "database": Secrets.MYSQL_DATABASE,
    }

    if Config.MYSQL_CONNECTION_POOL_SIZE:
        db_config.update({"pool_size": Config.MYSQL_CONNECTION_POOL_SIZE})

    db_connection = mysql.connector.connect(**db_config)
    cursor = db_connection.cursor(buffered=True)

    try:
        yield cursor
    finally:
        db_connection.commit()
        cursor.close()
        db_connection.close()


def _replace_further_occurances(text: str, old: str, new: str) -> str:
    offset = text.index(old) + 1
    return text[:offset] + text[offset:].replace(old, new)


class Storage:
    """The global object-relational mapping."""

    TABLES = [
        {
            "name": Config.POMS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.POMS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    userID BIGINT(20),
                    descript VARCHAR(30),
                    time_set TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    current_session TINYINT(1),
                    PRIMARY KEY(id)
                );
            """,
            "alterations": []
        },
        {
            "name": Config.EVENTS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.EVENTS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    event_name VARCHAR(100) NOT NULL,
                    pom_goal INT(11),
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    PRIMARY KEY(id)
                );
            """,
            "alterations": []
        },
        {
            "name": Config.USERS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.USERS_TABLE} (
                    userID BIGINT(20) NOT NULL UNIQUE,
                    timezone VARCHAR(8) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    inventory_string TEXT(30000),
                    player_level TINYINT(1) NOT NULL DEFAULT 1,
                    attack_level TINYINT(1) NOT NULL DEFAULT 1,
                    heavy_attack_level TINYINT(1) NOT NULL DEFAULT 1,
                    defend_level TINYINT(1) NOT NULL DEFAULT 1,
                    PRIMARY KEY(userID)
                );
            """,
            "alterations": [
                {
                    "condition": f"""
                        SELECT COUNT(*) FROM information_schema.columns
                        WHERE table_schema = '{Secrets.MYSQL_DATABASE}'
                        AND table_name = '{Config.USERS_TABLE}'
                        AND column_name = 'guildID';
                    """,
                    "alter_query": f"""
                        ALTER TABLE {Config.USERS_TABLE}
                        ADD guildID BIGINT(20) NOT NULL DEFAULT 0;
                    """
                }
            ]
        },
        {
            "name": Config.ACTIONS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.ACTIONS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    userID BIGINT(20),
                    team VARCHAR(10) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    was_successful TINYINT(1) NOT NULL,
                    was_critical TINYINT(1),
                    items_dropped VARCHAR(30),
                    damage INT(4),
                    time_set TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(id)
                );
            """,
            "alterations": []
        },
    ]

    @classmethod
    def create_tables_if_not_exists(cls):
        """Create predefined DB tables if they don't already exist."""
        for table in cls.TABLES:
            table_name, table_create_query, alterations = table.values()
            _log.info('Creating "%s" table, if it does not exist', table_name)

            with _mysql_database_cursor() as cursor:
                cursor.execute(table_create_query)

                for alteration in alterations:
                    condition, alter_query = alteration.values()
                    cursor.execute(condition)
                    result, = cursor.fetchone()

                    if not result:
                        cursor.execute(alter_query)

    @classmethod
    def delete_all_rows_from_all_tables(cls):
        """Delete all rows from all tables.

        This is a dangerous function and should only be run by developers on
        development machines.
        """
        _log.info("Deleting tables... ")
        with _mysql_database_cursor() as cursor:
            for table_name in (table["name"] for table in cls.TABLES):
                cursor.execute(f"DELETE FROM {table_name};")
        _log.info("Tables deleted.")

    @staticmethod
    def add_poms_to_user_session(
        user: DiscordUser,
        descript: str,
        count: int,
        time_set: dt = None,
    ):
        """Add a number of user poms."""
        query = f"""
            INSERT INTO {Config.POMS_TABLE} (
                userID,
                descript,
                time_set,
                current_session
            )
            VALUES (%s, %s, %s, %s);
        """

        descript = descript or None
        time_set = time_set or dt.now()
        poms = [(user.id, descript, time_set, True) for _ in range(count)]

        with _mysql_database_cursor() as cursor:
            cursor.executemany(query, poms)

    @staticmethod
    def clear_user_session_poms(user: DiscordUser):
        """Set all active session poms to be non-active."""
        query = f"""
            UPDATE  {Config.POMS_TABLE}
            SET current_session = 0
            WHERE userID = %s
            AND current_session = 1;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @staticmethod
    def delete_all_user_poms(user: DiscordUser):
        """Remove all poms for user."""
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @staticmethod
    def delete_most_recent_user_poms(user: DiscordUser, count: int):
        """Delete `count` most recent poms for `user`."""
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s
            ORDER BY time_set DESC
            LIMIT %s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, count))

    @staticmethod
    def get_ongoing_events() -> List[Event]:
        """Return a list of ongoing Events."""
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE start_date <= %s
            AND end_date >= %s;
        """

        current_date = dt.now()

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (current_date, current_date))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def get_poms(*,
                 user: DiscordUser = None,
                 date_range: DateRange = None) -> List[Pom]:
        """Get a list of poms from storage matching certain criteria.

        @param user Only match poms for this user.
        @param date_range Only match poms within this date range.
        @return List of Pom objects.
        """
        query = [f"SELECT * FROM {Config.POMS_TABLE}"]
        args = []

        if user:
            query += [f"WHERE userID=%s"]
            args += [user.id]

        if date_range:
            query += ["WHERE time_set >= %s", "AND time_set <= %s"]
            args += [date_range.start_date, date_range.end_date]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        with _mysql_database_cursor() as cursor:
            cursor.execute(query_str, args)
            rows = cursor.fetchall()

        return [Pom(*row) for row in rows]

    @staticmethod
    def add_new_event(name: str, goal: int, date_range: DateRange):
        """Add a new event row."""
        query = f"""
            INSERT INTO {Config.EVENTS_TABLE} (
                event_name,
                pom_goal,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s);
        """
        args = name, goal, date_range.start_date, date_range.end_date

        with _mysql_database_cursor() as cursor:
            try:
                cursor.execute(query, args)
            except mysql.connector.DatabaseError as exc:
                # Give a nicer error message than the mysql default.
                raise pombot.errors.EventCreationError(exc.msg)

    @staticmethod
    def get_all_events() -> List[Event]:
        """Return a list of all events."""
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            ORDER BY start_date;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def get_overlapping_events(date_range: DateRange) -> List[Event]:
        """Return a list of events in the database which overlap with the
        dates specified.
        """
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE %s < end_date
            AND %s > start_date;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (date_range.start_date, date_range.end_date))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def delete_event(name: str):
        """Delete the named event from the DB."""
        query = f"""
            DELETE FROM {Config.EVENTS_TABLE}
            WHERE event_name=%s
            ORDER BY start_date
            LIMIT 1;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (name, ))

    @staticmethod
    def add_user(user_id: int, zone: timezone, team: Team, guild_id: str):
        """Add a user into the users table."""
        query = f"""
            INSERT INTO {Config.USERS_TABLE} (
                userID,
                timezone,
                team,
                guildID
            )
            VALUES (%s, %s, %s, %s);
        """

        zone_str = time(tzinfo=zone).strftime('%z')
        values = user_id, zone_str, team.value, guild_id

        with _mysql_database_cursor() as cursor:
            try:
                cursor.execute(query, values)
            except mysql.connector.errors.IntegrityError as exc:
                user = Storage.get_user_by_id(user_id)
                raise pombot.errors.UserAlreadyExistsError(user) from exc

    @staticmethod
    def update_user(
        user_id: str,
        *,
        team: Team = None,
        guild_id: int = None,
        zone: timezone = None,
    ):
        """Set the user team."""
        updates = []
        values = []

        if team:
            updates += ["team=%s"]
            values += [team.value]

        if guild_id:
            updates += ["guildID=%s"]
            values += [guild_id]

        if zone:
            updates += ["timezone=%s"]
            values += [zone]

        if not updates:
            return

        query = f"""
            UPDATE {Config.USERS_TABLE}
            SET {", ".join(updates)}
            WHERE userID=%s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (*values, user_id))

    @staticmethod
    def get_team_populations() -> Tuple[int, int]:
        """Get the number of players on each team.

        @return Two numbers, the number of users on Knights and the number of
        users on Vikings.
        """
        query = f"""
            SELECT
                SUM(IF(team = '{Team.KNIGHTS}', 1, 0)),
                SUM(IF(team = '{Team.VIKINGS}', 1, 0))
            FROM {Config.USERS_TABLE};
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        if None in rows[0]:
            return 0, 0

        return tuple([int(row) for row in rows[0]])

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[PombotUser]:
        """Return a single user by its userID."""
        query = f"""
            SELECT * FROM {Config.USERS_TABLE}
            WHERE userID=%s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()

        if not row:
            raise pombot.errors.UserDoesNotExistError()

        return PombotUser(*row)

    @staticmethod
    def get_users_by_id(user_ids: List[int]) -> Set[PombotUser]:
        """Return a list of users from a list of userID's.

        This is a small optimization function to call the storage a single
        time to return multiple unique users, instead of calling it one time
        for each user.
        """
        if not user_ids:
            return []

        query = [f"SELECT * FROM {Config.USERS_TABLE}"]
        values = []

        for user_id in user_ids:
            query += ["WHERE userID=%s"]
            values += [user_id]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "OR")

        with _mysql_database_cursor() as cursor:
            cursor.execute(query_str, values)
            rows = cursor.fetchall()

        return {PombotUser(*r) for r in rows}

    @staticmethod
    def add_pom_war_action(
        user: DiscordUser,
        team: Team,
        action_type: ActionType,
        was_successful: bool,
        was_critical: bool,
        items_dropped: str,
        damage: int,
        time_set: dt,
    ):
        """Add an action to the ledger."""
        query = f"""
            INSERT INTO {Config.ACTIONS_TABLE} (
                userID,
                team,
                type,
                was_successful,
                was_critical,
                items_dropped,
                damage,
                time_set
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (user.id, team.value, action_type.value, was_successful,
                  was_critical, items_dropped, (damage or 0) * 100, time_set)

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, values)

    @staticmethod
    def get_actions(
        *,
        action_type: ActionType = None,
        user: DiscordUser = None,
        team: Team = None,
        was_successful = None,
        date_range: DateRange = None,
    ) -> List[Action]:
        """Get a list of actions from storage matching certain criteria.

        @param user Only match actions for this user.
        @param date_range Only match actions within this date range.
        @return List of Action objects.
        """
        query = [f"SELECT * FROM {Config.ACTIONS_TABLE}"]
        values = []

        if action_type:
            query += [f"WHERE type=%s"]
            values += [action_type.value]

        if user:
            query += [f"WHERE userID=%s"]
            values += [user.id]

        if team:
            query += [f"WHERE team=%s"]
            values += [team.value]

        if was_successful:
            query += [f"WHERE was_successful=%s"]
            values += [1]

        if date_range:
            query += ["WHERE time_set >= %s", "AND time_set <= %s"]
            values += [date_range.start_date, date_range.end_date]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        with _mysql_database_cursor() as cursor:
            cursor.execute(query_str, values)
            rows = cursor.fetchall()


        return [Action(*row) for row in rows]
