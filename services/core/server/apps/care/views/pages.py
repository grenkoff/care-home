"""Pages of care rendered on the server."""

from typing import final

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views import View

from server.apps.care.logic.usecases import list_services
from server.common.di import HasContainer
from server.common.money import Cents


@final
class Contacts(View):
    """Page that tells how to reach the care home."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Renders the address, phone, e-mail, visiting hours and map link."""
        return render(
            request,
            'care/contacts.html',
            {
                'phone': settings.SITE_PHONE,
                'email': settings.SITE_EMAIL,
                'map_url': settings.SITE_MAP_URL,
            },
        )


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
