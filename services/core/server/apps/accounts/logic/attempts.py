"""Codes given to an authenticator app, counted against a lock."""

import enum
from datetime import datetime
from typing import final

import attrs

from server.apps.accounts.logic.codes import Key, Totp
from server.apps.accounts.logic.constants import CODE_ATTEMPTS, CODE_LOCK
from server.apps.accounts.logic.errors import WrongCodeError


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
        if self._moment < ledger.locked_until:
            return Outcome(ledger=ledger, verdict=Verdict.locked)
        totp = Totp(Key(ledger.key), ledger.used_step)
        try:
            step = totp.accepted(self._code, self._moment)
        except WrongCodeError:
            return Outcome(ledger=self._failed(ledger), verdict=Verdict.wrong)
        return Outcome(
            ledger=attrs.evolve(ledger, used_step=step, failures=0),
            verdict=Verdict.accepted,
        )

    def _failed(self, ledger: Ledger) -> Ledger:
        """Counts a wrong code and locks the codes after too many in a row."""
        failures = ledger.failures + 1
        if failures < CODE_ATTEMPTS:
            return attrs.evolve(ledger, failures=failures)
        return attrs.evolve(
            ledger,
            failures=0,
            locked_until=self._moment + CODE_LOCK,
        )
