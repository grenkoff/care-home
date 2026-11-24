"""Database models of enquiries."""

import uuid
from typing import final, override

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from server.apps.enquiries.logic.constants import NAME_MAX_LENGTH, PHONE_MAX_LENGTH


@final
class Enquiry(models.Model):
    """Request of a visitor to be called back."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    name = models.CharField(_('name'), max_length=NAME_MAX_LENGTH)
    phone = models.CharField(_('phone'), max_length=PHONE_MAX_LENGTH)
    message = models.TextField(_('message'), blank=True)
    sent_at = models.DateTimeField(_('sent'), default=timezone.now, editable=False)
    handled = models.BooleanField(_('handled'), default=False)

    class Meta:
        """Order of enquiries for staff: the newest first."""

        ordering = ('-sent_at',)
        verbose_name = _('enquiry')
        verbose_name_plural = _('enquiries')

    @override
    def __str__(self) -> str:
        """Returns the name of the visitor."""
        return self.name
