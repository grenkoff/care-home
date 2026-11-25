"""Objects of accounts, built for the composition root."""

from datetime import timedelta

import punq
from django.conf import settings

from server.apps.accounts.infra import invitations, sources
from server.apps.accounts.logic.usecases import accept_invitation, invite_relative


def inject(container: punq.Container) -> None:
    """Registers the objects of accounts."""
    stored = invitations.StoredInvitations()
    opened = accept_invitation.OpenInvitation(stored, sources.SystemClock())
    container.register(
        invite_relative.InviteRelative,
        factory=lambda: invite_relative.InviteRelative(
            sources.SystemTokens(),
            sources.SystemClock(),
            timedelta(days=settings.INVITATION_DAYS),
        ),
    )
    container.register(accept_invitation.OpenInvitation, instance=opened)
    container.register(
        accept_invitation.AcceptInvitation,
        instance=accept_invitation.AcceptInvitation(stored, sources.SystemClock()),
    )
