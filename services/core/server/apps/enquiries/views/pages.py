"""Pages of enquiries rendered on the server."""

from typing import final

from django.views import View


@final
class Send(View):
    """Page that takes the enquiry of a visitor."""
