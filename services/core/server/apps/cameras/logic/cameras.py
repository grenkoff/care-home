"""Cameras of the common areas, as staff keep them and pages show them."""

import uuid
from typing import Protocol, final

import attrs

from server.common.bilingual import Bilingual


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Camera:
    """Camera as staff keep it: its id and its name in both languages."""

    id: uuid.UUID
    name: Bilingual


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Screen:
    """Camera as a page in one language shows it."""

    id: uuid.UUID
    name: str


class Cameras(Protocol):
    """Cameras that staff keep."""

    def active(self) -> tuple[Camera, ...]:
        """Returns the cameras that relatives may watch, in the order of names."""

    def found(self, camera: uuid.UUID) -> Camera:
        """Returns the active camera of the id or raises UnknownCameraError."""


class Journal(Protocol):
    """Journal of who opened which camera and when."""

    def record(self, viewer: uuid.UUID, camera: uuid.UUID) -> None:
        """Writes down that the viewer opened the camera now."""
