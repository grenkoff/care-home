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
_GARDEN: Final = Camera(id=uuid.uuid7(), name=Bilingual(russian='Сад', english='Garden'))


@final
@attrs.define(slots=True, frozen=True)
class _Viewers:
    """Fake viewers: only the one viewer of the tests is admitted."""

    def admitted(self, viewer: uuid.UUID) -> bool:
        """Tells whether the viewer is the viewer of the tests."""
        return viewer == _VIEWER


@final
@attrs.define(slots=True, frozen=True)
class _Cameras:
    """Fake cameras: the garden is the only active one."""

    def active(self) -> tuple[Camera, ...]:
        """Returns the garden."""
        return (_GARDEN,)

    def found(self, camera: uuid.UUID) -> Camera:
        """Returns the garden or raises UnknownCameraError."""
        if camera != _GARDEN.id:
            raise UnknownCameraError(camera)
        return _GARDEN


@final
@attrs.define(slots=True, frozen=True)
class _Journal:
    """Fake journal that keeps the viewings in a list."""

    opened: list[tuple[uuid.UUID, uuid.UUID]] = attrs.field(factory=list)

    def record(self, viewer: uuid.UUID, camera: uuid.UUID) -> None:
        """Appends the viewing to the list."""
        self.opened.append((viewer, camera))


def test_lists_the_active_cameras_in_the_language() -> None:
    screens = ListCameras(_Viewers(), _Cameras())(_VIEWER, 'ru')

    assert screens == [Screen(id=_GARDEN.id, name='Сад')]


def test_lists_no_camera_to_a_viewer_who_is_not_admitted() -> None:
    with pytest.raises(NotAdmittedError):
        ListCameras(_Viewers(), _Cameras())(_STRANGER, 'en')


def test_opens_a_camera_in_the_language() -> None:
    screen = OpenCamera(_Viewers(), _Cameras(), _Journal())(_VIEWER, _GARDEN.id, 'en')

    assert screen == Screen(id=_GARDEN.id, name='Garden')


def test_records_who_opened_the_camera() -> None:
    journal = _Journal()

    OpenCamera(_Viewers(), _Cameras(), journal)(_VIEWER, _GARDEN.id, 'en')

    assert journal.opened == [(_VIEWER, _GARDEN.id)]


def test_opens_no_camera_to_a_viewer_who_is_not_admitted() -> None:
    journal = _Journal()

    with pytest.raises(NotAdmittedError):
        OpenCamera(_Viewers(), _Cameras(), journal)(_STRANGER, _GARDEN.id, 'en')
    assert not journal.opened


def test_opens_no_unknown_camera() -> None:
    journal = _Journal()

    with pytest.raises(UnknownCameraError):
        OpenCamera(_Viewers(), _Cameras(), journal)(_VIEWER, uuid.uuid7(), 'en')
    assert not journal.opened
