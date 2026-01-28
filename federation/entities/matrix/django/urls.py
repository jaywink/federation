# noinspection PyPackageRequirements
from django.urls import re_path
# noinspection PyPackageRequirements
from django.views.decorators.csrf import csrf_exempt

from federation.entities.matrix.django.views import MatrixASTransactionsView

urlpatterns = [
    re_path(
        r"transactions/(?P<txn_id>[\w-]+)$",
        view=csrf_exempt(MatrixASTransactionsView.as_view()),
        name="matrix-as-transactions",
    ),
]
