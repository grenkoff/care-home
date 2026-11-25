"""Tests of the use cases that open and accept an invitation."""

from datetime import UTC, datetime, timedelta
from typing import Final, final

import attrs
import pytest

from server.apps.accounts.logic.errors import UnknownInvitationError
from server.apps.accounts.logic.invitations import Digest, Invitation
from server.apps.accounts.logic.usecases.accept_invitation import (
    AcceptInvitation,
    OpenInvitation,
)

_EXPIRY: Final = datetime(2026, 12, 1, 12, tzinfo=UTC)
_CODE: Final = 'code'


@final
@attrs.define(slots=True, frozen=True)
class _Stopped:
    """Fake: a clock that always shows the same moment."""

    moment: datetime

    def now(self) -> datetime:
        """Returns the moment."""
        return self.moment


@final
@attrs.define(slots=True, frozen=True)
class _Kept:
    """Fake: one invitation for a token, and the accepted ones in a list."""

    accepted: bool = False
    passwords: list[tuple[str, str]] = attrs.field(factory=list)

    def found(self, digest: str) -> Invitation:
        """Returns the invitation of the token or raises UnknownInvitationError."""
        if digest != Digest(_CODE).hexadecimal():
            raise UnknownInvitationError(digest)
        return Invitation(
            email='anna@example.test',
            expires_at=_EXPIRY,
            accepted=self.accepted,
        )

    def accept(self, digest: str, password: str) -> None:
        """Keeps the digest and the password."""
        self.passwords.append((digest, password))


def _opened(kept: _Kept, moment: datetime) -> OpenInvitation:
    """Returns the use case that opens invitations at the moment."""
    return OpenInvitation(kept, _Stopped(moment))


def test_open_invitation_names_its_email() -> None:
    opened = _opened(_Kept(), _EXPIRY - timedelta(seconds=1))

    assert opened(_CODE) == 'anna@example.test'


@pytest.mark.parametrize(
    ('kept', 'moment', 'code'),
    [
        (_Kept(accepted=True), _EXPIRY - timedelta(days=1), _CODE),
        (_Kept(), _EXPIRY, _CODE),
        (_Kept(), _EXPIRY + timedelta(days=1), _CODE),
        (_Kept(), _EXPIRY - timedelta(days=1), 'guess'),
    ],
)
def test_closed_invitation_is_refused(
    kept: _Kept,
    moment: datetime,
    code: str,
) -> None:
    with pytest.raises(UnknownInvitationError):
        _opened(kept, moment)(code)


def test_accepted_invitation_sets_the_password() -> None:
    kept = _Kept()

    AcceptInvitation(_opened(kept, _EXPIRY - timedelta(days=1)), kept)(
        _CODE,
        'a long secret',
    )

    assert kept.passwords == [(Digest(_CODE).hexadecimal(), 'a long secret')]


def test_expired_invitation_sets_no_password() -> None:
    kept = _Kept()

    with pytest.raises(UnknownInvitationError):
        AcceptInvitation(_opened(kept, _EXPIRY), kept)(_CODE, 'a long secret')

    assert not kept.passwords
