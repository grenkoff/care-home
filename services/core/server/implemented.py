"""Composition root: builds the use cases of every module with their parts."""

import punq

from server.composition import care, outbox


def populate_dependencies(container: punq.Container) -> punq.Container:
    """Registers the objects of every module in the container."""
    care.inject(container)
    outbox.inject(container)
    return container
