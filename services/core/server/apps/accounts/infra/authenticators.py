"""Authenticator apps kept in the database of accounts."""

import uuid
from datetime import datetime
from typing import final

import attrs
from django.db import transaction

from server.apps.accounts import models
from server.apps.accounts.logic.codes import Authenticator, Key


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

    def use(self, user: uuid.UUID, code: str, moment: datetime) -> None:
        """Keeps the step of a fresh valid code under the lock of the row."""
        with transaction.atomic():
            stored = models.Authenticator.objects.select_for_update().get(user_id=user)
            stored.used_step = Authenticator(
                Key(stored.key),
                stored.used_step,
            ).accepted(code, moment)
            stored.save(update_fields=['used_step'])
