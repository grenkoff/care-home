"""Tests of codes given to an authenticator app against its lock."""

import base64
from datetime import UTC, datetime, timedelta
from typing import Final

import attrs

from server.apps.accounts.logic.attempts import Attempt, Ledger, Outcome, Verdict

_MOMENT: Final = datetime.fromtimestamp(59, tz=UTC)
_RIGHT: Final = '287082'
_WRONG: Final = '000000'
_OPEN: Final = Ledger(
    key=base64.b32encode(b'12345678901234567890').decode(),
    used_step=0,
    failures=2,
    locked_until=datetime.fromtimestamp(0, tz=UTC),
)


def test_valid_code_keeps_its_step() -> None:
    assert Attempt(_RIGHT, _MOMENT).outcome(_OPEN) == Outcome(
        ledger=attrs.evolve(_OPEN, used_step=1, failures=0),
        verdict=Verdict.accepted,
    )


def test_wrong_code_counts_one_more_failure() -> None:
    assert Attempt(_WRONG, _MOMENT).outcome(_OPEN) == Outcome(
        ledger=attrs.evolve(_OPEN, failures=3),
        verdict=Verdict.wrong,
    )


def test_fifth_wrong_code_locks_the_codes() -> None:
    ledger = attrs.evolve(_OPEN, failures=4)

    assert Attempt(_WRONG, _MOMENT).outcome(ledger) == Outcome(
        ledger=attrs.evolve(
            ledger,
            failures=0,
            locked_until=_MOMENT + timedelta(minutes=15),
        ),
        verdict=Verdict.wrong,
    )


def test_right_code_is_refused_while_locked() -> None:
    ledger = attrs.evolve(_OPEN, locked_until=_MOMENT + timedelta(seconds=1))

    assert Attempt(_RIGHT, _MOMENT).outcome(ledger) == Outcome(
        ledger=ledger,
        verdict=Verdict.locked,
    )


def test_codes_are_checked_once_the_lock_ends() -> None:
    ledger = attrs.evolve(_OPEN, locked_until=_MOMENT)

    assert Attempt(_RIGHT, _MOMENT).outcome(ledger).verdict == Verdict.accepted
