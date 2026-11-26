"""Relay of the outbox with the subscribers of every topic."""

import punq

from server.apps.accounts.public import events
from server.apps.residents.infra import accounts
from server.common.outbox.relay import Relay


def inject(container: punq.Container) -> None:
    """Registers the relay with the subscribers of every topic."""
    container.register(
        Relay,
        instance=Relay({events.ACCOUNT_OPENED: (accounts.CopiedAccounts(),)}),
    )
