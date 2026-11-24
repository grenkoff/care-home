"""Routes of the pages of care."""

from django.urls import path

from server.apps.care.views import pages

urlpatterns = [
    path('services/', pages.Services.as_view(), name='services'),
]
