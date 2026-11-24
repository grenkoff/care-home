"""Routes of the pages of care."""

from django.urls import path

from server.apps.care.views import pages

urlpatterns = [
    path('', pages.Home.as_view(), name='home'),
    path('services/', pages.Services.as_view(), name='services'),
]
