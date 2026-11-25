"""Objects of accounts, built for the composition root."""

from datetime import timedelta

import punq
from django.conf import settings

from server.apps.accounts.infra import authenticators, invitations, sources
from server.apps.accounts.logic.usecases import (
    accept_invitation,
    check_code,
    connect_authenticator,
    invite_relative,
)


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
    _inject_authenticators(container)


def _inject_authenticators(container: punq.Container) -> None:
    """Registers the use cases of authenticator apps."""
    stored = authenticators.StoredAuthenticators()
    container.register(
        connect_authenticator.OfferKey,
        instance=connect_authenticator.OfferKey(sources.SystemKeys()),
    )
    container.register(
        connect_authenticator.HasAuthenticator,
        instance=connect_authenticator.HasAuthenticator(stored),
    )
    container.register(
        connect_authenticator.ConnectAuthenticator,
        instance=connect_authenticator.ConnectAuthenticator(
            stored,
            sources.SystemClock(),
        ),
    )
    container.register(
        check_code.CheckCode,
        instance=check_code.CheckCode(stored, sources.SystemClock()),
    )
