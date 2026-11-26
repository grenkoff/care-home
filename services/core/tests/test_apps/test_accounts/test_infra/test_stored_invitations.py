"""Tests of the invitations kept in the database of accounts."""

import hashlib
from datetime import timedelta
from typing import Final

import pytest
from django.utils import timezone

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.logic.errors import TakenEmailError, UnknownInvitationError
from server.apps.accounts.models import Invitation, User
from server.apps.accounts.public.events import ACCOUNT_OPENED
from server.common.outbox.models import Event
from server.common.outbox.outbox import StoredOutbox

_STORED: Final = StoredInvitations(StoredOutbox())
_CHOSEN: Final = 'a long secret'


@pytest.mark.django_db
def test_invitation_is_accepted_only_once(invitation: Invitation) -> None:
    _STORED.accept(invitation.digest, _CHOSEN, timezone.now())

    with pytest.raises(UnknownInvitationError):
        _STORED.accept(invitation.digest, 'another', timezone.now())


@pytest.mark.django_db
def test_expired_invitation_is_not_accepted(invitation: Invitation) -> None:
    with pytest.raises(UnknownInvitationError):
        _STORED.accept(
            invitation.digest,
            'a long secret of anna',
            invitation.expires_at,
        )

    assert not User.objects.exists()


@pytest.mark.django_db
def test_invitation_is_accepted_until_it_expires(invitation: Invitation) -> None:
    _STORED.accept(
        invitation.digest,
        'a long secret of anna',
        invitation.expires_at - timedelta(microseconds=1),
    )

    assert User.objects.filter(username=invitation.email).exists()


@pytest.mark.django_db
def test_taken_email_keeps_the_invitation_open(invitation: Invitation) -> None:
    User.objects.create_user(username=invitation.email)

    with pytest.raises(TakenEmailError):
        _STORED.accept(invitation.digest, _CHOSEN, timezone.now())

    invitation.refresh_from_db()
    assert invitation.accepted_at is None


@pytest.mark.django_db
def test_accepting_publishes_the_opened_account(invitation: Invitation) -> None:
    _STORED.accept(invitation.digest, _CHOSEN, timezone.now())

    assert list(
        Event.objects.values_list('topic', 'payload__account', 'payload__email'),
    ) == [(ACCOUNT_OPENED, str(User.objects.get().pk), invitation.email)]


@pytest.mark.django_db
def test_a_refused_invitation_publishes_nothing(invitation: Invitation) -> None:
    with pytest.raises(UnknownInvitationError):
        _STORED.accept(invitation.digest, _CHOSEN, invitation.expires_at)

    assert not Event.objects.exists()


@pytest.mark.django_db
def test_unknown_digest_is_refused() -> None:
    with pytest.raises(UnknownInvitationError):
        _STORED.found(hashlib.sha256(b'guess').hexdigest())
