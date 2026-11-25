"""Invitations kept in the database of accounts."""

from typing import final

import attrs
from django.db import transaction
from django.utils import timezone

from server.apps.accounts import models
from server.apps.accounts.logic.errors import TakenEmailError, UnknownInvitationError
from server.apps.accounts.logic.invitations import Invitation


@final
@attrs.define(slots=True, frozen=True)
class StoredInvitations:
    """Invitations kept in the table of accounts."""

    def found(self, digest: str) -> Invitation:
        """Returns the invitation of a digest or raises UnknownInvitationError."""
        stored = (
            models.Invitation.objects
            .filter(digest=digest)
            .only('email', 'expires_at', 'accepted_at')
            .first()
        )
        if stored is None:
            raise UnknownInvitationError(digest)
        return Invitation(
            email=stored.email,
            expires_at=stored.expires_at,
            accepted=stored.accepted_at is not None,
        )

    def accept(self, digest: str, password: str) -> None:
        """Makes the account of an unused invitation or raises an error."""
        with transaction.atomic():
            stored = (
                models.Invitation.objects
                .select_for_update()
                .filter(digest=digest, accepted_at__isnull=True)
                .first()
            )
            if stored is None:
                raise UnknownInvitationError(digest)
            if models.User.objects.filter(username__iexact=stored.email).exists():
                raise TakenEmailError(digest)
            models.User.objects.create_user(
                username=stored.email,
                email=stored.email,
                password=password,
            )
            stored.accepted_at = timezone.now()
            stored.save(update_fields=['accepted_at'])
