"""Tests of the use case that checks the code of an authenticator app."""

import uuid
from datetime import UTC, datetime
from typing import Final, final

import attrs

from server.apps.accounts.logic.usecases.check_code import CheckCode

_NOW: Final = datetime(2026, 11, 25, 12, tzinfo=UTC)
_USER: Final = uuid.UUID(int=1)


@final
@attrs.define(slots=True, frozen=True)
class _Stopped:
    """Fake: a clock that always shows the same moment."""

    def now(self) -> datetime:
        """Returns the moment."""
        return _NOW


@final
@attrs.define(slots=True, frozen=True)
class _Kept:
    """Fake: codes that are kept in a list when used."""

    used: list[tuple[uuid.UUID, str, datetime]] = attrs.field(factory=list)

    def use(self, user: uuid.UUID, code: str, moment: datetime) -> None:
        """Keeps the user, the code and the moment."""
        self.used.append((user, code, moment))


def test_code_is_used_at_the_current_moment() -> None:
    kept = _Kept()

    CheckCode(kept, _Stopped())(_USER, '287082')

    assert kept.used == [(_USER, '287082', _NOW)]
