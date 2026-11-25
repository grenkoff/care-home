"""Tests of the invitations kept in the database of accounts."""

import hashlib

import pytest

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.logic.errors import TakenEmailError, UnknownInvitationError
from server.apps.accounts.models import Invitation, User


@pytest.mark.django_db
def test_invitation_is_accepted_only_once(invitation: Invitation) -> None:
    StoredInvitations().accept(invitation.digest, 'a long secret of anna')

    with pytest.raises(UnknownInvitationError):
        StoredInvitations().accept(invitation.digest, 'another secret')


@pytest.mark.django_db
def test_taken_email_keeps_the_invitation_open(invitation: Invitation) -> None:
    User.objects.create_user(username=invitation.email)

    with pytest.raises(TakenEmailError):
        StoredInvitations().accept(invitation.digest, 'a long secret of anna')

    invitation.refresh_from_db()
    assert invitation.accepted_at is None


@pytest.mark.django_db
def test_unknown_digest_is_refused() -> None:
    with pytest.raises(UnknownInvitationError):
        StoredInvitations().found(hashlib.sha256(b'guess').hexdigest())
