# noinspection PyPackageRequirements
from django.conf.urls import url
# noinspection PyPackageRequirements
from django.urls import include

urlpatterns = [
    url(r'', include("federation.hostmeta.django.urls")),
    url(r'ap/', include("federation.entities.activitypub.django.urls")),
    url(r'^_matrix/', include("federation.entities.matrix.django.urls")),
]
