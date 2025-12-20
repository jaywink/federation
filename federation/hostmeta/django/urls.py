# noinspection PyPackageRequirements
from django.urls import re_path

from federation.hostmeta.django import rfc7033_webfinger_view
from federation.hostmeta.django.generators import (
    nodeinfo2_view, matrix_client_wellknown_view, matrix_server_wellknown_view,
)

urlpatterns = [
    re_path(r'^.well-known/matrix/client$', matrix_client_wellknown_view, name="matrix-client-wellknown"),
    re_path(r'^.well-known/matrix/server$', matrix_server_wellknown_view, name="matrix-server-wellknown"),
    re_path(r'^.well-known/webfinger$', rfc7033_webfinger_view, name="rfc7033-webfinger"),
    re_path(r'^.well-known/x-nodeinfo2$', nodeinfo2_view, name="nodeinfo2"),
]
