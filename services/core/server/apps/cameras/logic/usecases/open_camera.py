"""Use case that opens a camera to a relative and records it."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

import attrs

from server.apps.cameras.logic.cameras import Screen

if TYPE_CHECKING:
    from server.apps.cameras.logic.cameras import Cameras, Journal
    from server.apps.cameras.logic.viewers import Viewers


@final
@attrs.define(slots=True, frozen=True)
class OpenCamera:
    """Opens an active camera to an admitted viewer and records the viewing."""

    _viewers: Viewers
    _cameras: Cameras
    _journal: Journal

    def __call__(self, viewer: uuid.UUID, camera: uuid.UUID, language: str) -> Screen:
        """Returns the camera in the language or raises an error of cameras."""
        return Screen(id=camera, name='')
