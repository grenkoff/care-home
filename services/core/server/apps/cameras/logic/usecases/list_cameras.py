"""Use case that lists the cameras a relative may watch."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

import attrs

from server.apps.cameras.logic.cameras import Screen
from server.apps.cameras.logic.errors import NotAdmittedError

if TYPE_CHECKING:
    from server.apps.cameras.logic.cameras import Cameras
    from server.apps.cameras.logic.viewers import Viewers


@final
@attrs.define(slots=True, frozen=True)
class ListCameras:
    """Lists the active cameras in one language to an admitted viewer."""

    _viewers: Viewers
    _cameras: Cameras

    def __call__(self, viewer: uuid.UUID, language: str) -> tuple[Screen, ...]:
        """Returns the active cameras or raises NotAdmittedError."""
        if not self._viewers.admitted(viewer):
            raise NotAdmittedError(viewer)
        return tuple(
            Screen(id=camera.id, name=camera.name.said_in(language))
            for camera in self._cameras.active()
        )
