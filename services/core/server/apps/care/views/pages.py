"""Pages of care rendered on the server."""

from typing import final

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views import View

from server.apps.care.logic.usecases import list_services
from server.common.di import HasContainer
from server.common.money import Cents


@final
class Home(View):
    """Home page that introduces the care home."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Renders the introduction in the language of the page."""
        return render(request, 'care/home.html')


@final
class Services(HasContainer, View):
    """Page that lists the care services with their monthly prices."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Renders the care services in the language of the page."""
        services = self.resolve(list_services.ListServices)(get_language())
        return render(
            request,
            'care/services.html',
            {
                'services': [
                    (service, Cents(service.price_cents)) for service in services
                ],
            },
        )
