# noinspection PyPackageRequirements
from django.conf.urls import url
# noinspection PyPackageRequirements
from django.views.decorators.csrf import csrf_exempt

from federation.entities.matrix.django.views import MatrixASTransactionsView

urlpatterns = [
    url(
        regex=r"transactions/(?P<txn_id>[\w-]+)$",
        view=csrf_exempt(MatrixASTransactionsView.as_view()),
        name="matrix-as-transactions",
    ),
]
