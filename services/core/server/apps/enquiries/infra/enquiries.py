"""Enquiries kept in the database of enquiries."""

from typing import final

import attrs

from server.apps.enquiries import models
from server.apps.enquiries.logic.enquiries import Enquiry


@final
@attrs.define(slots=True, frozen=True)
class StoredEnquiries:
    """Enquiries kept in the table of enquiries."""

    def add(self, enquiry: Enquiry) -> None:
        """Writes the enquiry for staff, not handled yet."""
        models.Enquiry.objects.create(
            name=enquiry.name,
            phone=enquiry.phone,
            message=enquiry.message,
        )
