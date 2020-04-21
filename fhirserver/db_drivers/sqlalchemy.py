"""
This module has several functions that returns the correct expression to filter a query for SQLAlchemy
"""
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy import func
from sqlalchemy.sql import sqltypes
from sqlalchemy import between
from datetime import timedelta, datetime


def equal(item: QueryableAttribute, expected):
    """
    Return a SQLAlchemy case-insensitive equality constrain
    :param item:
    :param expected:
    :return:
    """
    return item.ilike(expected)


def exact(item: QueryableAttribute, expected):
    """
    Return a SQLAlchemy equality constrain
    :param item: The attribute to check
    :param expected: The value that the :arg:attribute should be equal to
    :return: a BinaryExpresion to pass to a SQLAlchemy filter_by
    """
    return item == expected


def not_equal(item: QueryableAttribute, expected):
    """
    Return a SQLAlchemy unequality constrain
    :param item: The attribute to check
    :param expected: The value that the :arg:attribute should not be equal to
    :return: a BinaryExpresion to pass to a SQLAlchemy filter_by
    """
    return item != expected


def contains(item: QueryableAttribute, expected: bool):
    """
    Return a SQLAlchemy constrain that represents a :contains modifier FHIR operation. It is implemented
    as a LIKE %expected% SQL operation
    :param item: 
    :param expected: 
    :return: 
    """
    return item.like('%{}%'.format(expected))


def missing(item: QueryableAttribute, expected):
    """
    Return a SQLAlchemy contrain that check if :arg:`item` is None if :arg:`true_or_false` is True,
    is not None if it's False
    :param item:
    :param expected:
    :return:
    """
    # Note that using `is None` or `is not None` will not generate a SQLAlchemy expression

    if expected is True:
        return item == None
    else:
        return item != None


def date_eq(item: QueryableAttribute, expected: datetime):
    return func.DATE(item) == func.DATE(expected)


def date_ne(item: QueryableAttribute, expected: datetime):
    return func.DATE(item) != func.DATE(expected)


def date_lt(item: QueryableAttribute, expected: datetime):
    if isinstance(item.property.columns[0].type, sqltypes.Date):
        # that's because FHIR spec states that if the date is e.g 1985-10-12 and the queried value is
        # 1985-10-12T10:00:00 than 1985-10-12 shall be included
        return date_le(item, expected)
    else:
        return func.DATETIME(item) < func.DATETIME(expected)


def date_gt(item: QueryableAttribute, expected: datetime):
    if isinstance(item.property.columns[0].type, sqltypes.Date):
        # that's because FHIR spec states that, if the date is e.g 1985-10-12 and the queried value is
        # 1985-10-12T10:00:00 than 1985-10-12 shall be included
        return date_ge(item, expected)
    else:
        return func.DATETIME(item) > func.DATETIME(expected)


def date_le(item: QueryableAttribute, expected: datetime):
    if isinstance(item.property.columns[0].type, sqltypes.Date):
        return func.DATE(item) <= func.DATE(expected)
    else:
        return func.DATETIME(item) <= func.DATETIME(expected)


def date_ge(item: QueryableAttribute, expected: datetime):
    if isinstance(item.property.columns[0].type, sqltypes.Date):
        return func.DATE(item) >= func.DATE(expected)
    else:
        return func.DATETIME(item) >= func.DATETIME(expected)


def date_ap(item: QueryableAttribute, expected: datetime):
    """
    Date is approximately equal. Approximately means at discretion of the implementation. Here for dates we set
    approximation between one day before and one day after the required value
    :param item:
    :param expected:
    :return:
    """
    delta = timedelta(days=1)
    if isinstance(item.property.columns[0].type, sqltypes.Date):
        return between(func.DATE(item), func.DATE(expected - delta), func.DATE(expected + delta))
    else:
        return between(func.DATETIME(item), func.DATETIME(expected - delta), func.DATETIME(expected + delta))
