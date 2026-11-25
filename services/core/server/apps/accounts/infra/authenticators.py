"""Authenticator apps kept in the database of accounts."""

import uuid
from typing import final

import attrs

from server.apps.accounts import models


@final
@attrs.define(slots=True, frozen=True)
class StoredAuthenticators:
    """Authenticator apps as rows of the database."""

    def connected(self, user: uuid.UUID) -> bool:
        """Tells whether the user has a row."""
        return models.Authenticator.objects.filter(user_id=user).exists()

    def connect(self, user: uuid.UUID, key: str, step: int) -> None:
        """Adds the row of the user."""
        models.Authenticator.objects.create(user_id=user, key=key, used_step=step)
