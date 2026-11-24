"""Tests of the relay that delivers events from the outbox."""

from typing import Final, final
from uuid import UUID, uuid7

import attrs
import pytest

from server.common.outbox.models import Event
from server.common.outbox.relay import Envelope, Relay

_TOPIC: Final = 'tests.v1.first'


def _pending(topic: str, text: str) -> UUID:
    """Keeps an event of the topic in the outbox and returns its id."""
    identifier = uuid7()
    Event.objects.create(
        id=identifier,
        topic=topic,
        payload={'id': str(identifier), 'text': text},
    )
    return identifier


@final
@attrs.define(frozen=True)
class _Inbox:
    """Fake: subscriber that keeps every envelope it receives."""

    received: list[Envelope] = attrs.field(factory=list)

    def receive(self, envelope: Envelope) -> None:
        """Keeps the envelope."""
        self.received.append(envelope)


@final
class _SubscriberError(RuntimeError):
    """Raised by a subscriber that cannot handle events."""

    __slots__ = ()


@final
@attrs.define(frozen=True)
class _Broken:
    """Fake: subscriber that fails on every event."""

    def receive(self, envelope: Envelope) -> None:
        """Fails to handle the envelope."""
        raise _SubscriberError(str(envelope.id))


@pytest.mark.django_db
def test_failed_delivery_leaves_the_event_pending() -> None:
    _pending(_TOPIC, 'retried')
    inbox = _Inbox()

    with pytest.raises(_SubscriberError):
        Relay({_TOPIC: (_Broken(),)}).deliver()

    assert Relay({_TOPIC: (inbox,)}).deliver()
    assert len(inbox.received) == 1


@pytest.mark.django_db
def test_relay_delivers_pending_events_by_topic() -> None:
    first = _pending(_TOPIC, 'first')
    _pending('tests.v1.other', 'other')
    inbox = _Inbox()
    relay = Relay({_TOPIC: (inbox,)})

    deliveries = [relay.deliver() for _ in range(3)]

    assert deliveries == [True, True, False]
    assert inbox.received == [
        Envelope(first, {'id': str(first), 'text': 'first'}),
    ]
    assert not Event.objects.exists()
