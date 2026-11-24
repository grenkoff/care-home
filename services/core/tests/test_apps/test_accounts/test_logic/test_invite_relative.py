"""Tests of the use case that invites a relative."""

from datetime import UTC, datetime, timedelta
from typing import Final, final

import attrs

from server.apps.accounts.logic.invitations import Issued
from server.apps.accounts.logic.usecases.invite_relative import InviteRelative

_NOW: Final = datetime(2026, 11, 24, 12, tzinfo=UTC)


@final
@attrs.define(slots=True, frozen=True)
class _Stopped:
    """Fake: a clock that always shows the same moment."""

    def now(self) -> datetime:
        """Returns the moment."""
        return _NOW


@final
@attrs.define(slots=True, frozen=True)
class _Same:
    """Fake: tokens that are always the same."""

    def fresh(self) -> str:
        """Returns the token."""
        return 'token'


def test_invitation_keeps_a_digest_and_an_expiry() -> None:
    issued = InviteRelative(_Same(), _Stopped(), timedelta(days=7))()

    assert issued == Issued(
        code='token',
        digest='3c469e9d6c5875d37a43f353d4f88e61fcf812c66eee3457465a40b0da4153e0',
        expires_at=datetime(2026, 12, 1, 12, tzinfo=UTC),
    )
