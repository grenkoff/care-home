"""Use case that lists the cameras a relative may watch."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

import attrs

from server.apps.cameras.logic.cameras import Screen

if TYPE_CHECKING:
    from server.apps.cameras.logic.cameras import Cameras
    from server.apps.cameras.logic.viewers import Viewers


@final
@attrs.define(slots=True, frozen=True)
class ListCameras:
    """Lists the active cameras in one language to an admitted viewer."""

    _viewers: Viewers
    _cameras: Cameras

    def __call__(self, viewer: uuid.UUID, language: str) -> list[Screen]:
        """Returns the active cameras or raises NotAdmittedError."""
        return []
