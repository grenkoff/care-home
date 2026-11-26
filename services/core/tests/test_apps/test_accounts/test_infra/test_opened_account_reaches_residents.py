"""Tests that an accepted invitation reaches residents through the relay."""

import punq
import pytest
from django.utils import timezone

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.models import Invitation, User
from server.apps.residents.logic.usecases.find_relative import FindRelative
from server.common.outbox.outbox import StoredOutbox
from server.common.outbox.relay import Relay
from server.implemented import populate_dependencies


@pytest.mark.django_db
def test_the_relay_makes_the_account_linkable(
    invitation: Invitation,
) -> None:
    container = populate_dependencies(punq.Container())
    StoredInvitations(StoredOutbox()).accept(
        invitation.digest,
        'a long secret',
        timezone.now(),
    )

    container.resolve(Relay).deliver()

    assert container.resolve(FindRelative)(invitation.email) == User.objects.get().pk
