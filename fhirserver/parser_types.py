import importlib
from enum import Enum

from dateutil.parser import isoparse
from flask_restful.reqparse import Argument
# from flask import current_app
#

from fhirserver.db_drivers import sqlalchemy as db_driver

# FHIRPrefixes = ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'gt', 'sa', 'eb', 'ap')


class FHIRPrefixes(object):
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    LT = 'lt'
    GE = 'ge'
    LE = 'le'
    SA = 'sa'
    EB = 'eb'
    AP = 'ap'

    @classmethod
    def values(cls):
        return cls.__dict__.values()


class FHIRModifiers(object):
    MISSING = ':missing'
    EXACT = ':exact'
    CONTAINS = ':contains'
    TEXT = ':text'
    NOT = ':not'
    IN = ':in'
    NOT_IN = ':not-in'
    BELOW = ':below'
    ABOVE = ':above'
    IDENTIFIER = ':identifier'


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


def _check_operator(value, operator, allowed_modifiers):
    if operator not in allowed_modifiers and operator is not None:
        raise ValueError

    if operator == FHIRModifiers.MISSING and value not in ('true', 'false'):
        raise ValueError


class BaseFHIRSearch(object):

    OPERATORS = ('=', FHIRModifiers.MISSING)

    def __init__(self, value, name=None, operator='='):

        _check_operator(value, operator, self.OPERATORS)

        self.modifier = operator.replace('=', '') if operator != '=' and operator is not None else None

        if self.modifier == FHIRModifiers.MISSING:
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

            if operation not in FHIRPrefixes.values():
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
            if operation in FHIRPrefixes.values():
                # note that the method raises a Value Error if it fails, as required by Flask Restful
                self.value = isoparse(datestr)
                self.operation = operation
            else:
                raise ValueError

    def get_query_condition(self, item):
        if self.modifier == FHIRModifiers.MISSING:
            return db_driver.missing(item, self.value)
        elif self.operation == FHIRPrefixes.EQ:
            return db_driver.date_eq(item, self.value)
        elif self.operation == FHIRPrefixes.NE:
            return db_driver.date_ne(item, self.value)
        elif self.operation in (FHIRPrefixes.LT, FHIRPrefixes.EB):
            return db_driver.date_lt(item, self.value)
        elif self.operation in (FHIRPrefixes.GT, FHIRPrefixes.SA):
            return db_driver.date_gt(item, self.value)
        elif self.operation == FHIRPrefixes.LE:
            return db_driver.date_le(item, self.value)
        elif self.operation == FHIRPrefixes.GE:
            return db_driver.date_ge(item, self.value)
        elif self.operation == FHIRPrefixes.AP:
            return db_driver.date_ap(item, self.value)


class FHIRString(BaseFHIRSearch):

    OPERATORS = ('=', FHIRModifiers.MISSING, FHIRModifiers.EXACT, FHIRModifiers.CONTAINS)

    def __init__(self, value, name=None, operator='='):
        super(FHIRString, self).__init__(value, name, operator)
        if not isinstance(self.value, bool):
            self.value = value

    def get_query_condition(self, item):
        if self.modifier is None:
            return db_driver.equal(item, self.value)
        elif self.modifier == FHIRModifiers.EXACT:
            return db_driver.exact(item, self.value)
        elif self.modifier == FHIRModifiers.MISSING:
            return db_driver.missing(item, self.value)
        elif self.modifier == FHIRModifiers.CONTAINS:
            return db_driver.contains(item, self.value)


class FHIRToken(BaseFHIRSearch):

    OPERATORS = ('=', FHIRModifiers.MISSING, FHIRModifiers.TEXT, FHIRModifiers.NOT,
                 FHIRModifiers.IN, FHIRModifiers.NOT_IN, FHIRModifiers.BELOW, FHIRModifiers.ABOVE)

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

    OPERATORS = ['=', FHIRModifiers.MISSING, FHIRModifiers.IDENTIFIER, FHIRModifiers.ABOVE, FHIRModifiers.BELOW]

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
    OPERATORS = ('=', FHIRModifiers.MISSING, FHIRModifiers.ABOVE, FHIRModifiers.BELOW)

    def __init__(self, value, name=None, operator='='):
        super(FHIRUri, self).__init__(value, name, operator)

        if self.value is None:
            self.value = value


def query_argument_type_factory(name, typ, dest=None):
    try:
        typ_handler = FHIRSearchTypes.get_type_handler(typ)
    except KeyError:
        raise Exception('Unkown argument type')

    return Argument(name, dest=dest, type=typ_handler, operators=typ_handler.OPERATORS,
                    required=False, location='args')
