"""Routes of the pages of residents."""

from django.urls import path

from server.apps.residents.views import pages

urlpatterns = [
    path('family/', pages.Family.as_view(), name='family'),
]
