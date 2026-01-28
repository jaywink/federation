# noinspection PyPackageRequirements
from django.urls import re_path
# noinspection PyPackageRequirements
from django.urls import include

urlpatterns = [
    re_path(r'', include("federation.hostmeta.django.urls")),
    re_path(r'ap/', include("federation.entities.activitypub.django.urls")),
    re_path(r'^matrix/', include("federation.entities.matrix.django.urls")),
]
