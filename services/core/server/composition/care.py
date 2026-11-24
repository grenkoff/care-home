"""Objects of care, built for the composition root."""

import punq

from server.apps.care.infra import offers
from server.apps.care.logic.usecases import list_services


def inject(container: punq.Container) -> None:
    """Registers the objects of care."""
    container.register(
        list_services.ListServices,
        instance=list_services.ListServices(offers.StoredOffers()),
    )
