"""Database models of residents."""

import uuid
from typing import final, override

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from server.apps.residents.logic.constants import (
    FULL_NAME_MAX_LENGTH,
    KIND_MAX_LENGTH,
)


@final
class Resident(models.Model):
    """Person who lives or lived in the home."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    full_name = models.CharField(_('full name'), max_length=FULL_NAME_MAX_LENGTH)
    moved_in_on = models.DateField(_('moved in'))
    moved_out_on = models.DateField(_('moved out'), null=True, blank=True)

    class Meta:
        """Order of residents for staff: by name."""

        ordering = ('full_name',)
        verbose_name = _('resident')
        verbose_name_plural = _('residents')

    @override
    def __str__(self) -> str:
        """Returns the full name of the resident."""
        return self.full_name


@final
class Kind(models.TextChoices):
    """Kinship of a relative to a resident."""

    spouse = 'spouse', _('spouse')
    child = 'child', _('child')
    grandchild = 'grandchild', _('grandchild')
    sibling = 'sibling', _('sibling')
    other = 'other', _('other relative')


@final
class Kinship(models.Model):
    """Link through which a relative may follow a resident."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    resident = models.ForeignKey(
        Resident,
        on_delete=models.PROTECT,
        related_name='kinships',
        verbose_name=_('resident'),
    )
    kind = models.CharField(
        _('kinship'),
        max_length=KIND_MAX_LENGTH,
        choices=Kind.choices,
    )
    relative = models.UUIDField(_('relative'))
    granted_by = models.UUIDField(_('granted by'), editable=False)
    granted_at = models.DateTimeField(
        _('granted'),
        default=timezone.now,
        editable=False,
    )
    revoked_at = models.DateTimeField(
        _('revoked'),
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        """Order of links for staff: the latest first."""

        ordering = ('-granted_at',)
        verbose_name = _('kinship')
        verbose_name_plural = _('kinships')

    @override
    def __str__(self) -> str:
        """Returns the resident and the kinship."""
        return f'{self.resident}: {self.get_kind_display()}'
