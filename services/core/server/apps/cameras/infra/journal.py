"""Journal of viewings kept in the database of cameras."""

import uuid
from typing import final

import attrs

from server.apps.cameras import models


@final
@attrs.define(slots=True, frozen=True)
class StoredJournal:
    """Viewings kept in the table of viewings."""

    def record(self, viewer: uuid.UUID, camera: uuid.UUID) -> None:
        """Writes down that the viewer opened the camera now."""
        models.Viewing.objects.create(viewer=viewer, camera_id=camera)
