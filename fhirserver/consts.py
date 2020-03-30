from collections import namedtuple


class ISSUE_SEVERITY:
    FATAL = 'fatal'
    ERROR = 'error'
    WARNING = 'warning'
    INFORMATION = 'information'


class ISSUE_TYPE:
    INVALID = 'invalid'
    STRUCTURE = 'structure'
    REQUIRED = 'required'
    VALUE = 'value'
    INVARIANT = 'invariant'

    PROCESSING = 'processing'
    NOT_SUPPORTED = 'not-supported'
    DUPLICATE = 'duplicate'
    MULTIPLE_MATCHES = 'multiple-matches'
    NOT_FOUND = 'not-found'
