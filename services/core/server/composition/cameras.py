"""Objects of cameras, built for the composition root."""

import punq

from server.apps.cameras.infra import cameras, journal, viewers
from server.apps.cameras.logic.usecases import list_cameras, open_camera
from server.apps.residents.public.kin import Kin


def inject(container: punq.Container, kin: Kin) -> None:
    """Registers the objects of cameras with the facade of residents."""
    admitted = viewers.KinViewers(kin)
    kept = cameras.StoredCameras()
    container.register(
        list_cameras.ListCameras,
        instance=list_cameras.ListCameras(admitted, kept),
    )
    container.register(
        open_camera.OpenCamera,
        instance=open_camera.OpenCamera(admitted, kept, journal.StoredJournal()),
    )
