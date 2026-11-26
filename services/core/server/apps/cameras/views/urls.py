"""Routes of the pages of cameras."""

from django.urls import path

from server.apps.cameras.views import pages

urlpatterns = [
    path('cameras/', pages.Cameras.as_view(), name='cameras'),
    path('cameras/<uuid:camera>/', pages.Camera.as_view(), name='camera'),
]
