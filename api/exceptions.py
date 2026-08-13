"""API exception behavior, including conflict status preservation."""

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, ValidationError) and response is not None:
        codes = str(exc.get_codes())
        if "conflict" in codes:
            response.status_code = 409
        else:
            response.status_code = 422
        if isinstance(response.data, list) and len(response.data) == 1:
            response.data = {"detail": str(response.data[0])}
        elif isinstance(response.data, dict) and set(response.data) == {"non_field_errors"}:
            errors = response.data["non_field_errors"]
            response.data = {"detail": str(errors[0]) if len(errors) == 1 else errors}
    return response
