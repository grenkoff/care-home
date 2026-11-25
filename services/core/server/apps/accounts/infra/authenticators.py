"""Authenticator apps kept in the database of accounts."""

import uuid
from datetime import datetime
from typing import final

import attrs
from django.db import transaction

from server.apps.accounts import models
from server.apps.accounts.logic.attempts import Attempt, Ledger, Verdict
from server.apps.accounts.logic.errors import LockedCodesError, WrongCodeError


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
        """Checks a code under the lock of the row and keeps what it changed."""
        with transaction.atomic():
            stored = (
                models.Authenticator.objects
                .select_for_update()
                .filter(user_id=user)
                .first()
            )
            if stored is None:
                raise WrongCodeError
            verdict = self._kept(stored, Attempt(code, moment))
        match verdict:
            case Verdict.wrong:
                raise WrongCodeError
            case Verdict.locked:
                raise LockedCodesError
            case Verdict.accepted:
                return

    def _kept(self, stored: models.Authenticator, attempt: Attempt) -> Verdict:
        """Saves the row after an attempt and returns the verdict on it."""
        outcome = attempt.outcome(
            Ledger(
                key=stored.key,
                used_step=stored.used_step,
                failures=stored.failures,
                locked_until=stored.locked_until,
            ),
        )
        stored.used_step = outcome.ledger.used_step
        stored.failures = outcome.ledger.failures
        stored.locked_until = outcome.ledger.locked_until
        stored.save(update_fields=['used_step', 'failures', 'locked_until'])
        return outcome.verdict
