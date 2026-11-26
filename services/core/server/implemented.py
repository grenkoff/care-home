"""Composition root: builds the use cases of every module with their parts."""

import punq

from server.composition import accounts, care, enquiries, outbox, residents


def populate_dependencies(container: punq.Container) -> punq.Container:
    """Registers the objects of every module in the container."""
    facade_of_accounts = accounts.inject(container)
    care.inject(container)
    enquiries.inject(container)
    residents.inject(container, facade_of_accounts)
    outbox.inject(container)
    return container
