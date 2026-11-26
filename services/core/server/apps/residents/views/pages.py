"""Pages of residents rendered on the server."""

from typing import final

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from server.common.di import HasContainer


@final
class Family(HasContainer, View):
    """Page where a relative sees the residents they follow."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Shows the residents of the relative who signed in."""
        return render(request, 'residents/family.html', {'members': ()})
