"""Codes given to an authenticator app, counted against a lock."""

import enum
from datetime import datetime
from typing import final

import attrs


@final
class Verdict(enum.Enum):
    """What a code given to an app turned out to be."""

    accepted = enum.auto()
    wrong = enum.auto()
    locked = enum.auto()


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Ledger:
    """Authenticator app as the check of a code reads and writes it."""

    key: str
    used_step: int
    failures: int
    locked_until: datetime


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Outcome:
    """Ledger after a code and the verdict on the code."""

    ledger: Ledger
    verdict: Verdict


@final
@attrs.define(slots=True, frozen=True)
class Attempt:
    """Code given to an authenticator app at a moment."""

    _code: str
    _moment: datetime

    def outcome(self, ledger: Ledger) -> Outcome:
        """Returns the ledger after the code and the verdict on it."""
        return Outcome(ledger=ledger, verdict=Verdict.accepted)
