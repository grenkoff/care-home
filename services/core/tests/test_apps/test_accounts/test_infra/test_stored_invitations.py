"""Tests of the invitations kept in the database of accounts."""

import hashlib

import pytest

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.logic.invitations import UnknownInvitationError
from server.apps.accounts.models import Invitation


@pytest.mark.django_db
def test_invitation_is_accepted_only_once(invitation: Invitation) -> None:
    StoredInvitations().accept(invitation.digest, 'a long secret of anna')

    with pytest.raises(UnknownInvitationError):
        StoredInvitations().accept(invitation.digest, 'another secret')


@pytest.mark.django_db
def test_unknown_digest_is_refused() -> None:
    with pytest.raises(UnknownInvitationError):
        StoredInvitations().found(hashlib.sha256(b'guess').hexdigest())
