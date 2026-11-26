"""Accounts that residents copy from the facts of accounts."""

from typing import final

import attrs

from server.common.outbox.relay import Envelope


@final
@attrs.define(slots=True, frozen=True)
class CopiedAccounts:
    """Observer: copies each opened account, once however often it comes."""

    def receive(self, envelope: Envelope) -> None:
        """Keeps the account under the id of its fact."""
