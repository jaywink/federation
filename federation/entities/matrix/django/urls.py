# noinspection PyPackageRequirements
from django.conf.urls import url
# noinspection PyPackageRequirements
from django.views.decorators.csrf import csrf_exempt

from federation.entities.matrix.django.views import MatrixASTransactionsView

urlpatterns = [
    csrf_exempt(url(
        regex=r"transactions/(?P<txn_id>[\w-]+)$",
        view=MatrixASTransactionsView.as_view(),
        name="matrix-as-transactions",
    )),
]
