"""Objects of enquiries, built for the composition root."""

import punq

from server.apps.enquiries.infra import enquiries
from server.apps.enquiries.logic.usecases import send_enquiry


def inject(container: punq.Container) -> None:
    """Registers the objects of enquiries."""
    container.register(
        send_enquiry.SendEnquiry,
        instance=send_enquiry.SendEnquiry(enquiries.StoredEnquiries()),
    )
