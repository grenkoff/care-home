"""Pages of residents rendered on the server."""

from typing import final

from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from server.apps.residents.logic.usecases import list_family
from server.apps.residents.models import KINDS
from server.common.di import HasContainer


@final
class Family(HasContainer, View):
    """Page where a relative sees the residents they follow."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Shows the residents of the relative or sends a visitor to sign in."""
        relative = request.user.pk
        if relative is None:
            return redirect_to_login(request.get_full_path())
        kinds = dict(KINDS)
        members = [
            (member.full_name, kinds[member.kind])
            for member in self.resolve(list_family.ListFamily)(relative)
        ]
        return render(request, 'residents/family.html', {'members': members})
