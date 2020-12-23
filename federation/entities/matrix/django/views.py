import logging

# noinspection PyPackageRequirements
from django.http import JsonResponse
# noinspection PyPackageRequirements
from django.views import View

from federation.utils.django import get_function_from_config
from federation.utils.matrix import get_matrix_configuration

logger = logging.getLogger("federation")


class MatrixASBaseView(View):
    def dispatch(self, request, *args, **kwargs):
        token = request.GET.get("access_token")
        if not token:
            return JsonResponse({"error": "M_FORBIDDEN"}, content_type='application/json', status=403)

        matrix_config = get_matrix_configuration()
        if token != matrix_config["appservice"]["token"]:
            return JsonResponse({"error": "M_FORBIDDEN"}, content_type='application/json', status=403)

        return super().dispatch(request, *args, **kwargs)


class MatrixASTransactionsView(MatrixASBaseView):
    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def put(self, request, *args, **kwargs):
        # Inject the transaction ID to the request as part of the meta items
        request.META["matrix_transaction_id"] = kwargs.get("txn_id")
        process_payload_function = get_function_from_config('process_payload_function')
        result = process_payload_function(request)

        if result:
            return JsonResponse({}, content_type='application/json', status=200)
        else:
            return JsonResponse({"error": "M_UNKNOWN"}, content_type='application/json', status=400)
