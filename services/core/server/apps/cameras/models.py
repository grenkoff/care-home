"""Database models of cameras."""

import uuid
from typing import final, override

from django.db import models
from django.utils.translation import gettext_lazy as _

from server.apps.cameras.logic.constants import NAME_MAX_LENGTH, STREAM_MAX_LENGTH


@final
class Camera(models.Model):
    """Camera of a common area with its name in Russian and English."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    name_ru = models.CharField(_('name in Russian'), max_length=NAME_MAX_LENGTH)
    name_en = models.CharField(_('name in English'), max_length=NAME_MAX_LENGTH)
    stream = models.SlugField(
        _('key of the stream'),
        max_length=STREAM_MAX_LENGTH,
        unique=True,
        help_text=_('The key under which the video service knows the camera.'),
    )
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        """Order of cameras: by the English name."""

        ordering = ('name_en',)
        verbose_name = _('camera')
        verbose_name_plural = _('cameras')

    @override
    def __str__(self) -> str:
        """Returns the English name of the camera."""
        return self.name_en
