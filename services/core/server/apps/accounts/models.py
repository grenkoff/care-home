"""Database models of the accounts module."""

import uuid
from typing import ClassVar, final, override

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from server.apps.accounts.logic.constants import DIGEST_LENGTH


@final
class Users(UserManager['User']):
    """Users found by the user name regardless of its case."""

    @override
    def get_by_natural_key(self, username: str | None) -> User:
        """Returns the user whose user name matches regardless of case."""
        return self.get(username__iexact=username)


@final
class User(AbstractUser):
    """Person who signs in, known by a UUIDv7."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    objects: ClassVar[Users] = Users()


@final
class Invitation(models.Model):
    """One-time link through which a relative gets an account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    email = models.EmailField(_('e-mail'))
    digest = models.CharField(max_length=DIGEST_LENGTH, unique=True, editable=False)
    expires_at = models.DateTimeField(_('expires'), editable=False)
    accepted_at = models.DateTimeField(
        _('accepted'),
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        """Order of invitations for staff: the latest first."""

        ordering = ('-expires_at',)
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')

    @override
    def __str__(self) -> str:
        """Returns the e-mail invited."""
        return self.email
