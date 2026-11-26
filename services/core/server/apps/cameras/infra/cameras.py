"""Cameras kept in the database of cameras."""

import uuid
from typing import final

import attrs

from server.apps.cameras import models
from server.apps.cameras.logic.cameras import Camera
from server.common.bilingual import Bilingual


@final
@attrs.define(slots=True, frozen=True)
class StoredCameras:
    """Cameras kept in the table of cameras."""

    def active(self) -> tuple[Camera, ...]:
        """Returns the cameras that relatives may watch, in the order of names."""
        return tuple(
            Camera(id=pk, name=Bilingual(russian=russian, english=english))
            for pk, russian, english in models.Camera.objects
            .filter(active=True)
            .order_by('name_en', 'id')
            .values_list('pk', 'name_ru', 'name_en')
        )

    def found(self, camera: uuid.UUID) -> Camera:
        """Returns the active camera of the id or raises UnknownCameraError."""
        raise NotImplementedError(camera)
