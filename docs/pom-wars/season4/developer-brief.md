# 2021 Summer Pom Event: Developer Brief

## Current state

### Configure Database

### Invoke Bot

- Test server group.
- Personal server.

### Run Tests

- `mock_discord`
- `make`

### Storage and Async

- ???

## Next actions

### The Map

- How the map is split?
  - Static 2 - 4 "tiers"?
  - Unequal number of tiers?
    - One team could reasonably have more "tiers"
      - This could give the player a choice for how they
        want to play.
      - Might be too complex for time scale.
      - Might give an underhanded advantage to some servers.
      - Might unfairly promote some servers.
  - Dynamic number of tiers based on player counts?
    - Not a good idea:
      - Players may not want a changing map outside of their
        control.
      - Probably too complex given time scales.
  - How is the map rendered?
    - Per player?
    - Global location?
    - Pinned message in a specific team channel?

### Drops

- DB (re-)configuration.
  - New table
    - Table changes during production (and test!)
    - Can one action possible drop multiple items?
      - If so, drops will need a uniq ID.
      - If not, drop ID's can share value with action ID.
        - Probably doesn't matter tho.
- When drops happen.
- How drops are used.
  - Automatically.
    - Can automatically-applied drops affect a single person
      or are they always whole-team things?
  - Via user command.
- How does the map affect drops?
  - Certain parts of the map drop more or less often?
  - Certain drops can only be achieved on some parts?
  - Etc.

### Stories

- New stories (N*M problem here...)
  - Missed actions.
  - Per team.
  - Per map location.
  - Per action type:
    - Attack
      - Critical
    - Heavy Attack
      - Critical
    - Defend
- In-code formatting.
  - Move to XML stories?
    - What should the XML look like?
    - XSD schemas?
      - Maybe not given time scales.
  - New folder structure for additional complexity?

### Artwork

- Who's doing this?
  - Vertical or horizontal map layout?
  - Split directly down the middle?
- What if the drawn image does not align with engineered
  system?

<!-- vim: tw=60 ts=2 sw=2 expandtab
 -->
