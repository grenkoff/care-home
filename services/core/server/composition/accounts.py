"""Objects of accounts, built for the composition root."""

from datetime import timedelta

import punq
from django.conf import settings

from server.apps.accounts.infra import sources
from server.apps.accounts.logic.usecases import invite_relative


def inject(container: punq.Container) -> None:
    """Registers the objects of accounts."""
    container.register(
        invite_relative.InviteRelative,
        factory=lambda: invite_relative.InviteRelative(
            sources.SystemTokens(),
            sources.SystemClock(),
            timedelta(days=settings.INVITATION_DAYS),
        ),
    )
