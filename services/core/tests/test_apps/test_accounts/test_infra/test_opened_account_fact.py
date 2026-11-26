"""Tests that an opened account and its fact are kept or lost together."""

from typing import final

import attrs
import pytest
from django.utils import timezone

from server.apps.accounts.infra.invitations import StoredInvitations
from server.apps.accounts.models import Invitation, User
from server.common.outbox.outbox import Fact


@final
class _OutboxError(RuntimeError):
    """Raised by the outbox of the tests."""

    __slots__ = ()


@final
@attrs.define(slots=True, frozen=True)
class _Broken:
    """Fake outbox that refuses every fact."""

    def add(self, topic: str, fact: Fact) -> None:
        """Refuses the fact."""
        raise _OutboxError(topic)


@pytest.mark.django_db
def test_a_lost_fact_leaves_no_account(invitation: Invitation) -> None:
    with pytest.raises(_OutboxError):
        StoredInvitations(_Broken()).accept(
            invitation.digest,
            'a long secret',
            timezone.now(),
        )

    invitation.refresh_from_db()
    assert (User.objects.exists(), invitation.accepted_at) == (False, None)
