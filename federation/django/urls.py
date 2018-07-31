from django.conf.urls import url
from django.urls import include

urlpatterns = [
    url(r'', include("federation.hostmeta.django.urls")),
    url(r'ap/', include("federation.entities.activitypub.django.urls")),
]
