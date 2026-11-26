"""Composition root: builds the use cases of every module with their parts."""

import punq

from server.composition import (
    accounts,
    cameras,
    care,
    enquiries,
    outbox,
    residents,
)


def populate_dependencies(container: punq.Container) -> punq.Container:
    """Registers the objects of every module in the container."""
    accounts.inject(container)
    care.inject(container)
    enquiries.inject(container)
    facade_of_residents = residents.inject(container)
    cameras.inject(container, facade_of_residents)
    outbox.inject(container)
    return container
