"""Outbox that keeps facts in the transaction of the change they report."""

from typing import Protocol, final
from uuid import UUID

import attrs
import msgspec
from django.db import transaction

from server.common.outbox.models import Event


@final
class OutsideTransactionError(RuntimeError):
    """Raised for a fact written outside the transaction of its change."""

    __slots__ = ()


class Fact(Protocol):
    """Fact with its own UUIDv7 id."""

    @property
    def id(self) -> UUID:
        """Returns the id of the fact."""


class Outbox(Protocol):
    """Place where facts wait until the relay delivers them."""

    def add(self, topic: str, fact: Fact) -> None:
        """Keeps the fact under the topic in the current transaction."""


@final
@attrs.define(slots=True, frozen=True)
class StoredOutbox:
    """Outbox kept in the database next to the data it reports."""

    def add(self, topic: str, fact: Fact) -> None:
        """Writes the fact as a pending event or raises OutsideTransactionError."""
        if not transaction.get_connection().in_atomic_block:
            raise OutsideTransactionError(topic)
        Event.objects.create(
            id=fact.id,
            topic=topic,
            payload=msgspec.to_builtins(fact),
        )
