"""Convenience file to "run" this package from the command line outside of a
test.
"""

from pombot.data.pom_wars import actions

print(actions.Attacks.get_random(
    team="Knight",
    average_daily_actions=17,
    critical=True,
    heavy=True,
).get_message())
