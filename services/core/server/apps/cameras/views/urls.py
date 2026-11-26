"""Routes of the pages of cameras."""

from django.urls import path
from django.views.decorators.cache import never_cache

from server.apps.cameras.views import pages

urlpatterns = [
    path('cameras/', never_cache(pages.Cameras.as_view()), name='cameras'),
    path(
        'cameras/<uuid:camera>/',
        never_cache(pages.Camera.as_view()),
        name='camera',
    ),
]
