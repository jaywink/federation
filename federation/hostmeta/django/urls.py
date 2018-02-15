from django.conf.urls import url

from federation.hostmeta.django import rfc3033_webfinger_view

urlpatterns = [
    url(r'^.well-known/webfinger$', rfc3033_webfinger_view, name="rfc3033-webfinger"),
]
