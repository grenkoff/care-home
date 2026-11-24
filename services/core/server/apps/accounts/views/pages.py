"""Pages of accounts rendered on the server."""

from typing import final

from django.views import View


@final
class Accept(View):
    """Page where a relative accepts an invitation."""
