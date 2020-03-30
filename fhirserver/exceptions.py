from fhirclient.models.fhirabstractbase import FHIRValidationError

from fhirserver import ISSUE_TYPE, ISSUE_SEVERITY


class Error:
    """
    A class with
    """
    def __init__(self, code, path, severity):
        self.code = code
        self.path = path
        self.severity = severity


class FHIRServerException(Exception):
    def __init__(self, message, http_code, errors):
        super(FHIRServerException, self).__init__(message)
        self.http_code = http_code
        self.errors = errors


class InvalidHeaderException(FHIRServerException):
    def __init__(self, http_code, data):
        errors = []
        for location, message in data['message'].items():
            error_path = location
            error_code = ISSUE_TYPE.REQUIRED if message.find('Missing') != -1 else ISSUE_TYPE.INVALID
            errors.append(Error(error_code, error_path, ISSUE_SEVERITY.FATAL))
        message = "Errors occurred getting request headers"
        super(InvalidHeaderException, self).__init__(message, http_code, errors)


class InvalidBodyException(FHIRServerException):
    """
    A FHIRServerException constructed from FHIRValidationError
    """
    def __init__(self, exception):
        errors = []
        for error in exception.errors:
            if isinstance(error, FHIRValidationError):
                error_path = error.path
            else:
                error_path = None
            if isinstance(error, KeyError):
                error_code = ISSUE_TYPE.REQUIRED
            else:
                error_code = ISSUE_TYPE.INVALID
            errors.append(Error(error_code, error_path, ISSUE_SEVERITY.FATAL))
        message = "Errors occurred getting data from request"
        super(InvalidBodyException, self).__init__(message, 400, errors)


class InvalidQueryParameterException(FHIRServerException):
    def __init__(self, http_code, data):
        errors = []
        for location, message in data['message'].items():
            error_path = location
            error_code = ISSUE_TYPE.REQUIRED if message.find('Missing') != -1 else ISSUE_TYPE.INVALID
            errors.append(Error(error_code, error_path, ISSUE_SEVERITY.FATAL))
        message = "Errors in query parameter(s) format"
        super(InvalidQueryParameterException, self).__init__(message, http_code, errors)


class NotFoundException(FHIRServerException):
    def __init__(self):
        message = "The resource was not found"
        errors = [
            Error(ISSUE_TYPE.NOT_FOUND, None, ISSUE_SEVERITY.ERROR)
        ]
        super(NotFoundException, self).__init__(message, 404, errors)
