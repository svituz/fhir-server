from enum import Enum

from dateutil.parser import isoparse
from flask_restful.reqparse import Argument

_prefixes = ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'gt', 'sa', 'eb', 'ap')


def _check_operator(value, operator, allowed_modifiers):
    if operator not in allowed_modifiers and operator is not None:
        raise ValueError

    if operator == ':missing=' and value not in ('true', 'false'):
        raise ValueError


class BaseFHIRSearch(object):

    OPERATORS = ('=', ':missing=')

    def __init__(self, value, name=None, operator='='):

        _check_operator(value, operator, self.OPERATORS)

        self.modifier = operator.replace('=', '') if operator != '=' and operator is not None else None

        if self.modifier == ':missing':
            self.value = value == 'true'
        else:
            self.value = None


class FHIRNumber(BaseFHIRSearch):
    """
    A fhir number parameter can be a number or a number prefixed with a modifier (e.g., 10, 10.0, ne10)
    """

    def __init__(self, value, name=None, operator='='):
        super(FHIRNumber, self).__init__(value, name, operator)
        if isinstance(self.value, bool):
            self.operation = None

        if self.value is None:
            operation, number = value[0:2], value[2:]

            if operation not in _prefixes:
                operation = 'eq'
                number = value

            for typ in (int, float):
                try:
                    self.value = typ(number)
                    self.operation = operation
                    break
                except ValueError:
                    continue
            else:
                raise ValueError


class FHIRDate(BaseFHIRSearch):

    def __init__(self, value, name=None, operator='='):
        super(FHIRDate, self).__init__(value, name, operator)
        if isinstance(self.value, bool):
            self.operation = None
        else:
            operation, datestr = value[0:2], value[2:]
            if operation in _prefixes:
                # note that the method raises a Value Error if it fails, as required by Flask Restful
                self.value = isoparse(datestr)
                self.operation = operation
            else:
                raise ValueError


class FHIRString(BaseFHIRSearch):

    OPERATORS = ('=', ':missing=', ':exact=', ':contains=')

    def __init__(self, value, name=None, operator='='):
        super(FHIRString, self).__init__(value, name, operator)
        if not isinstance(self.value, bool):
            self.value = value


class FHIRToken(BaseFHIRSearch):

    OPERATORS = ('=', ':missing=', ':not=', ':in=', ':not-in=', ':below=', ':above=')

    def __init__(self, value, name=None, operator='='):
        super(FHIRToken, self).__init__(value, name, operator)

        if isinstance(self.value, bool):
            self.system = None
        else:
            parts = value.split('|')

            if len(parts) == 1:
                system, code = '', value
            elif len(parts) == 2:
                system, code = parts
            else:
                raise ValueError

            self.system = system
            self.value = code


class FHIRReference(BaseFHIRSearch):

    OPERATORS = ['=', ':missing=', ':identifier=', ':above=', ':below=']

    def __init__(self, value, name=None, operator='='):
        # we reduce case like Observation?subject:Patient=23 to Observation?subject=Patient/23
        from fhirserver.resources import RESOURCES

        if operator in RESOURCES:
            value = '{}/{}'.format(operator, value)
            operator = None

        super(FHIRReference, self).__init__(value, name, operator)

        if isinstance(self.value, bool):
            self.type = None
        else:
            parts = value.split('/')
            if len(parts) == 1:
                typ = None  # value remains the same
            elif len(parts) == 2:
                typ, value = parts
            else:
                raise ValueError

            self.value = value
            self.type = typ


class FHIRQuantity(FHIRNumber):
    def __init__(self, value, name=None, operator='='):

        parts = value.split('|')
        if len(parts) == 2:  # it means we only have one of system|code which is not allowed
            raise ValueError
        elif len(parts) == 3:
            value, system, code = parts
        else:
            system, code = None, None

        super(FHIRQuantity, self).__init__(value, name, operator)
        if isinstance(self.value, bool):
            self.system = None
            self.code = None
        else:
            self.system = system
            self.code = code


class FHIRUri(BaseFHIRSearch):
    OPERATORS = ('=', ':missing=', ':above=', ':below=')

    def __init__(self, value, name=None, operator='='):
        super(FHIRUri, self).__init__(value, name, operator)

        if self.value is None:
            self.value = value


class FHIRSearchTypes(Enum):
    NUMBER = 1
    DATE = 2
    STRING = 3
    TOKEN = 4
    REFERENCE = 5
    QUANTITY = 6
    URI = 7

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_type_handler(cls, enum_value):
        typ_map = {
            cls.NUMBER: FHIRNumber,
            cls.DATE: FHIRDate,
            cls.STRING: FHIRString,
            cls.TOKEN: FHIRToken,
            cls.REFERENCE: FHIRReference,
            cls.QUANTITY: FHIRQuantity,
            cls.URI: FHIRUri
        }
        return typ_map[enum_value]


def query_argument_type_factory(name, typ, dest=None):
    try:
        typ_handler = FHIRSearchTypes.get_type_handler(typ)
    except KeyError:
        raise Exception('Unkown argument type')

    return Argument(name, dest=dest, type=typ_handler, operators=typ_handler.OPERATORS,
                    required=False, location='args')
