import enum
import json
from aiohttp import web


def _generate_specific_http_exception_class(cls):
    assert cls.sub_code is not None
    assert cls.error_reason != ''

    def __init__(self, reason=None, **kwargs):
        if reason is None:
            reason = self.error_reason
        body = {'error': kwargs,
                'error_reason': reason,
                'error_subcode': self.sub_code,
                'error_code': self.status_code}
        cls.__init__(self,
                     text=json.dumps(body),
                     content_type='application/json')

        return type(cls.__name__, (cls,),
                    {'__init__': __init__,
                     '__doc__': getattr(cls, '__doc__', '')})


@enum.unique
class ErrorCode(enum.IntEnum):
    # 400
    field_validation = 1
    object_exists = 2

    # 401
    invalid_login = 3
    no_access_token = 4
    invalid_access_token = 5

    # 403
    permission_denied = 6
    user_disabled = 7

    # 404
    object_not_found = 8


@_generate_specific_http_exception_class
class JsonBodyValidationError(web.HTTPBadRequest):
    """Raised if request json body doesn't valid"""
    sub_code = ErrorCode.field_validation
    error_reason = "Invalid JSON body"


@_generate_specific_http_exception_class
class ObjectAlreadyExist(web.HTTPBadRequest):
    """Raised if object already exist"""
    sub_code = ErrorCode.object_exists
    error_reason = "Object already exist"


@_generate_specific_http_exception_class
class InvalidLogin(web.HTTPUnauthorized):
    """Raised if user's login/password is invalid"""
    sub_code = ErrorCode.invalid_login
    error_reason = "Invalid username/password"


@_generate_specific_http_exception_class
class NoAccessTokenError(web.HTTPUnauthorized):
    """No Authorization header found"""
    sub_code = ErrorCode.no_access_token
    error_reason = "Authorization required"


@_generate_specific_http_exception_class
class InvalidAccessTokenError(web.HTTPUnauthorized):
    """Raised if access token or session is invalid"""
    sub_code = ErrorCode.invalid_access_token
    error_reason = "Invalid Authorization"


@_generate_specific_http_exception_class
class PermissionDenied(web.HTTPForbidden):
    """Raised if user hasn't got required permission for operation"""
    sub_code = ErrorCode.permission_denied
    error_reason = "Permission denied"


@_generate_specific_http_exception_class
class UserDisabled(web.HTTPForbidden):
    """Raised if user tries to login, but is disabled in system"""
    sub_code = ErrorCode.user_disabled
    error_reason = "User is disabled by administrator"


@_generate_specific_http_exception_class
class ObjectNotFound(web.HTTPNotFound):
    """Raised if requested object not found or object id is invalid"""
    sub_code = ErrorCode.object_not_found
    error_reason = "Object not found"
