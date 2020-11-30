import logging

from sanic.response import json
from sanic import Blueprint
from sanic.exceptions import SanicException

ERRORS_BP = Blueprint('errors')
LOGGER = logging.getLogger(__name__)
DEFAULT_MSGS = {
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    501: 'Not Implemented',
    503: 'Internal Error'
}


def add_status_code(code):
    def class_decorator(cls):
        cls.status_code = code
        return cls

    return class_decorator


class ApiException(SanicException):
    def __init__(self, message=None, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if message is None:
            self.message = DEFAULT_MSGS[self.status_code]
        else:
            self.message = message


@add_status_code(400)
class ApiBadRequest(ApiException):
    pass


@add_status_code(401)
class ApiUnauthorized(ApiException):
    pass


@add_status_code(403)
class ApiForbidden(ApiException):
    pass


@add_status_code(404)
class ApiNotFound(ApiException):
    pass


@add_status_code(501)
class ApiNotImplemented(ApiException):
    pass


@add_status_code(500)
class ApiInternalError(ApiException):
    pass


@ERRORS_BP.exception(ApiException)
def api_json_error(request, exception):
    return json({
        'error': exception.message
    }, status=exception.status_code)


@ERRORS_BP.exception(Exception)
def json_error(request, exception):
    try:
        code = exception.status_code
    except AttributeError:
        code = 500
    LOGGER.exception(exception)
    return json({
        'error': exception.args[0]
    }, status=code)
