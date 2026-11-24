"""Database models of care."""

import uuid
from typing import final, override

from django.db import models
from django.utils.translation import gettext_lazy as _

from server.apps.care.logic.constants import NAME_MAX_LENGTH


@final
class Service(models.Model):
    """Care service of the home with texts in Russian and English."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    position = models.PositiveSmallIntegerField(_('position'))
    name_ru = models.CharField(_('name in Russian'), max_length=NAME_MAX_LENGTH)
    name_en = models.CharField(_('name in English'), max_length=NAME_MAX_LENGTH)
    description_ru = models.TextField(_('description in Russian'))
    description_en = models.TextField(_('description in English'))
    price_cents = models.PositiveIntegerField(_('monthly price in cents'))

    class Meta:
        """Order and invariants of care services kept by the database."""

        ordering = ('position',)
        verbose_name = _('care service')
        verbose_name_plural = _('care services')
        constraints = (
            models.CheckConstraint(
                condition=models.Q(price_cents__gte=1),
                name='care_service_price_cents_positive',
            ),
        )

    @override
    def __str__(self) -> str:
        """Returns the English name of the care service."""
        return self.name_en
