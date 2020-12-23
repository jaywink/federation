# noinspection PyPackageRequirements
from django.conf.urls import url

from federation.entities.matrix.django.views import MatrixASTransactionsView

urlpatterns = [
    url(
        regex=r"transactions/(?P<txn_id>[\w-]+)$",
        view=MatrixASTransactionsView.as_view(),
        name="matrix-as-transactions",
    ),
]
