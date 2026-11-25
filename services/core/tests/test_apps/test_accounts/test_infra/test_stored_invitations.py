"""Tests of the invitations kept in the database of accounts."""

import hashlib
from datetime import timedelta

import pytest
from django.utils import timezone

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.logic.errors import TakenEmailError, UnknownInvitationError
from server.apps.accounts.models import Invitation, User


@pytest.mark.django_db
def test_invitation_is_accepted_only_once(invitation: Invitation) -> None:
    StoredInvitations().accept(invitation.digest, 'a long secret', timezone.now())

    with pytest.raises(UnknownInvitationError):
        StoredInvitations().accept(invitation.digest, 'another', timezone.now())


@pytest.mark.django_db
def test_expired_invitation_is_not_accepted(invitation: Invitation) -> None:
    with pytest.raises(UnknownInvitationError):
        StoredInvitations().accept(
            invitation.digest,
            'a long secret of anna',
            invitation.expires_at,
        )

    assert not User.objects.exists()


@pytest.mark.django_db
def test_invitation_is_accepted_until_it_expires(invitation: Invitation) -> None:
    StoredInvitations().accept(
        invitation.digest,
        'a long secret of anna',
        invitation.expires_at - timedelta(microseconds=1),
    )

    assert User.objects.filter(username=invitation.email).exists()


@pytest.mark.django_db
def test_taken_email_keeps_the_invitation_open(invitation: Invitation) -> None:
    User.objects.create_user(username=invitation.email)

    with pytest.raises(TakenEmailError):
        StoredInvitations().accept(invitation.digest, 'a long secret', timezone.now())

    invitation.refresh_from_db()
    assert invitation.accepted_at is None


@pytest.mark.django_db
def test_unknown_digest_is_refused() -> None:
    with pytest.raises(UnknownInvitationError):
        StoredInvitations().found(hashlib.sha256(b'guess').hexdigest())
