"""Collection of Pombot's errors."""


class EventError(Exception):
    "Base exception for event errors."
    def __init__(self, msg = None):
        super().__init__(msg or self.__class__.__doc__)
        self.msg = msg


class EventCreationError(EventError):
    "Failed to create event."


class TooManyEventsError(EventError):
    "Too many ongoing events."


class PomDescriptionError(Exception):
    "Base exception for pom description errors."
    def __init__(self, msg = None):
        super().__init__(msg or self.__class__.__doc__)
        self.msg = msg


class DescriptionTooLongError(PomDescriptionError):
    "Too many characters in pom description."
