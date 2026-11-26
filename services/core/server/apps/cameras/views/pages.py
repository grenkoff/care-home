"""Pages of cameras rendered on the server."""

from typing import final

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views import View
from django.views.decorators.cache import never_cache

from server.apps.cameras.logic.errors import NotAdmittedError
from server.apps.cameras.logic.usecases import list_cameras
from server.common.di import HasContainer


@final
class Cameras(HasContainer, View):
    """Page where an admitted relative sees the cameras of the home."""

    @method_decorator(never_cache)
    def get(self, request: HttpRequest) -> HttpResponse:
        """Shows the active cameras, refuses a stranger, sends a visitor to sign in."""
        viewer = request.user.pk
        if viewer is None:
            return redirect_to_login(request.get_full_path())
        try:
            screens = self.resolve(list_cameras.ListCameras)(viewer, get_language())
        except NotAdmittedError as error:
            raise PermissionDenied from error
        return render(request, 'cameras/cameras.html', {'screens': screens})
