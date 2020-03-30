import operator as op
from dateutil.parser import isoparse

_prefixes = ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'gt', 'sa', 'eb', 'ap')


def _check_modifier(value, modifier, allowed_modifiers):
    if modifier not in allowed_modifiers:
        raise ValueError
    if modifier == ':missing' and value not in ('true', 'false'):
        raise ValueError


def fhir_number(value, name=None, modifier=None):
    """
    A fhir number parameter can be a number or a number prefixed with a modifier (e.g., 10, 10.0, ne10)
    """
    _check_modifier(value, modifier, (None, ':missing'))

    if modifier == ':missing':
        return value == 'true', None, modifier

    operation, number = value[0:2], value[2:]
    if operation not in _prefixes:
        operation = 'eq'
        number = value

    for typ in (int, float):
        try:
            return typ(number), operation, modifier
        except ValueError:
            continue

    raise ValueError


def fhir_date(value, name=None, modifier=None):
    allowed_modifiers = (None, ':missing')
    _check_modifier(value, modifier, allowed_modifiers)

    if modifier == ':missing':
        return value == 'true', None, modifier

    operation, datestr = value[0:2], value[2:]
    if operation in _prefixes:
        # that the method raises a Value Error if it fails, as required by Flask Restful
        return isoparse(datestr), operation, modifier
    raise ValueError


def fhir_string(value, name=None, modifier=None):
    allowed_modifiers = (None, ':missing', ':exact', ':contains')
    _check_modifier(value, modifier, allowed_modifiers)

    if modifier == ':missing':
        return value == 'true', None, modifier

    return value, modifier


def fhir_token(value, name=None, modifier=None):
    allowed_modifiers = (None, ':missing', ':not', ':in', ':not-in', ':below', ':above')
    _check_modifier(value, modifier, allowed_modifiers)

    if modifier == ':missing':
        return value == 'true', None, modifier

    parts = value.split('|')
    if len(parts) == 1:
        system, code = '', value
    elif len(parts) == 2:
        system, code = parts
    else:
        raise ValueError
    return (system, code), modifier


def fhir_reference(value, name=None, modifier=None):
    from fhirserver.resources import RESOURCES

    allowed_modifiers = [None, ':missing', ':identifier', ':above', ':below'] + RESOURCES
    _check_modifier(value, modifier, allowed_modifiers)

    if modifier == ':missing':
        return value == 'true', None, modifier

    # we reduce case like Observation?subject:Patient=23 to Observation?subject=Patient/23
    if modifier in RESOURCES:
        value = '{}/{}'.format(modifier, value)
        modifier = None

    parts = value.split('/')
    if len(parts) == 1:
        typ = None  # value remains the same
    elif len(parts) == 2:
        typ, value = parts
    else:
        raise ValueError
    return typ, value, modifier


def fhir_quantity(value, name=None, modifier=None):
    # this will eventually fail in a ValueError
    allowed_modifiers = (None, ':missing')
    _check_modifier(value, modifier, allowed_modifiers)
    if modifier == ':missing':
        return value == 'true', None, modifier

    parts = value.split('|')
    if len(parts) == 2:  # it means we only have one of system|code which is not allowed
        raise ValueError
    elif len(parts) == 3:
        value, system, code = parts
    else:
        system, code = None, None

    value, operation, modifier = fhir_number(value)  # the first parameter follow the rules of fhir_number
    return value, operation, system, code, modifier


def fhir_uri(value, name=None, modifier=None):
    allowed_modifiers = (None, ':missing', ':above', ':below')
    _check_modifier(value, modifier, allowed_modifiers)
    if modifier == ':missing':
        return value == 'true', None, modifier
    return value, modifier
