"""Tests of the command that relays events from the outbox."""

import io
import os
import signal
from typing import final, override
from uuid import uuid7

import pytest
from django.core.management import call_command

from server.common.outbox.models import Event


@final
class _Terminating(io.StringIO):
    """Command output that sends SIGTERM to the process on the first write."""

    @override
    def write(self, text: str) -> int:
        """Keeps the text and asks the process to stop."""
        os.kill(os.getpid(), signal.SIGTERM)
        return super().write(text)


@pytest.mark.django_db
def test_relay_events_drains_outbox_on_sigterm() -> None:
    identifier = uuid7()
    Event.objects.create(
        id=identifier,
        topic='tests.v1.unheard',
        payload={'id': str(identifier)},
    )

    call_command('relay_events', stdout=_Terminating())

    assert not Event.objects.exists()
