"""Tests of the use cases through which relatives watch the cameras."""

import uuid
from typing import Final, final

import attrs
import pytest

from server.apps.cameras.logic.cameras import Camera, Screen
from server.apps.cameras.logic.errors import NotAdmittedError, UnknownCameraError
from server.apps.cameras.logic.usecases.list_cameras import ListCameras
from server.apps.cameras.logic.usecases.open_camera import OpenCamera
from server.common.bilingual import Bilingual

_VIEWER: Final = uuid.uuid7()
_STRANGER: Final = uuid.uuid7()
_ENGLISH: Final = 'en'
_GARDEN: Final = Camera(
    id=uuid.uuid7(),
    name=Bilingual(russian='Сад', english='Garden'),
)


@final
@attrs.define(slots=True, frozen=True)
class _Home:
    """Fake home: one admitted viewer, the garden and a journal in a list."""

    opened: list[tuple[uuid.UUID, uuid.UUID]] = attrs.field(factory=list)

    def admitted(self, viewer: uuid.UUID) -> bool:
        """Tells whether the viewer is the viewer of the tests."""
        return viewer == _VIEWER

    def active(self) -> tuple[Camera, ...]:
        """Returns the garden."""
        return (_GARDEN,)

    def found(self, camera: uuid.UUID) -> Camera:
        """Returns the garden or raises UnknownCameraError."""
        if camera != _GARDEN.id:
            raise UnknownCameraError(camera)
        return _GARDEN

    def record(self, viewer: uuid.UUID, camera: uuid.UUID) -> None:
        """Appends the viewing to the list."""
        self.opened.append((viewer, camera))


def test_lists_the_active_cameras_in_the_language() -> None:
    home = _Home()

    assert ListCameras(home, home)(_VIEWER, 'ru') == (
        Screen(id=_GARDEN.id, name='Сад'),
    )


def test_lists_nothing_to_a_stranger() -> None:
    home = _Home()

    with pytest.raises(NotAdmittedError):
        ListCameras(home, home)(_STRANGER, _ENGLISH)


def test_opens_a_camera_in_the_language() -> None:
    home = _Home()

    screen = OpenCamera(home, home, home)(_VIEWER, _GARDEN.id, _ENGLISH)

    assert screen == Screen(id=_GARDEN.id, name='Garden')


def test_records_who_opened_the_camera() -> None:
    home = _Home()

    OpenCamera(home, home, home)(_VIEWER, _GARDEN.id, _ENGLISH)

    assert home.opened == [(_VIEWER, _GARDEN.id)]


def test_opens_nothing_to_a_stranger() -> None:
    home = _Home()

    with pytest.raises(NotAdmittedError):
        OpenCamera(home, home, home)(_STRANGER, _GARDEN.id, _ENGLISH)
    assert not home.opened


def test_opens_no_unknown_camera() -> None:
    home = _Home()

    with pytest.raises(UnknownCameraError):
        OpenCamera(home, home, home)(_VIEWER, uuid.uuid7(), _ENGLISH)
    assert not home.opened
