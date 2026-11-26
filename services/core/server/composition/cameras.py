"""Objects of cameras, built for the composition root."""

import punq

from server.apps.cameras.infra import cameras, viewers
from server.apps.cameras.logic.usecases import list_cameras
from server.apps.residents.public.kin import Kin


def inject(container: punq.Container, kin: Kin) -> None:
    """Registers the objects of cameras with the facade of residents."""
    container.register(
        list_cameras.ListCameras,
        instance=list_cameras.ListCameras(
            viewers.KinViewers(kin),
            cameras.StoredCameras(),
        ),
    )
