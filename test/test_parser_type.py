import operator
from unittest import TestCase

from dateutil.parser import isoparse

from fhirserver.parser_types import fhir_number, fhir_date, fhir_string, fhir_token, fhir_reference, fhir_quantity, \
    fhir_uri
from fhirserver.resources import RESOURCES

_search_prefixes = ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'gt', 'sa', 'eb', 'ap')


class TestPatient(TestCase):

    def test_number_with_int_string(self):
        value, op, modifier = fhir_number("100")
        self.assertEqual(op, 'eq')
        self.assertEqual(value, 100)
        self.assertIsNone(modifier)

    def test_number_with_missing_modifier(self):
        value, op, modifier = fhir_number('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_number('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_number_with_float_string(self):
        value, op, modifier = fhir_number("100.00")
        self.assertEqual(op, 'eq')
        self.assertEqual(value, 100.00)
        self.assertIsNone(modifier)

        value, op, modifier = fhir_number("1e2")
        self.assertEqual(op, 'eq')
        self.assertEqual(value, 100.00)
        self.assertIsNone(modifier)

    def test_number_with_operator(self):
        for operation in ('lt', 'le', 'gt', 'ge', 'ne'):
            value, op, modifier = fhir_number("{}100".format(operation))
            self.assertEqual(op, operation)
            self.assertEqual(value, 100)
            self.assertIsNone(modifier)

            value, op, modifier = fhir_number("{}100.00".format(operation))
            self.assertEqual(op, operation)
            self.assertEqual(value, 100.00)
            self.assertIsNone(modifier)

    def test_wrong_number(self):
        self.assertRaises(ValueError, fhir_number, "st100", None, None)
        self.assertRaises(ValueError, fhir_number, "100,00", None, None)
        self.assertRaises(ValueError, fhir_number, "notanumber", None, None)
        self.assertRaises(ValueError, fhir_number, '100', None, ':missing')

    def test_date(self):
        for op in _search_prefixes:
            for date_str in ("2020", "2020-10", "2020-10-13", "2020-10-13T10", "2020-10-13T10:13",
                             "2020-10-13T10:13:15", "2020-10-13T10:13:15.123", "2020-10-13T10:13:15.123+02:00"):
                date, res_op, modifier = fhir_date("{}{}".format(op, date_str))
                self.assertEqual(res_op, op)
                self.assertEqual(date, isoparse(date_str))

    def test_date_with_missing_modifier(self):
        value, op, modifier = fhir_date('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_date('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_wrong_date(self):
        # wrong date values
        for op in _search_prefixes:
            for date_str in ("2020-", "10-13-2020", "10/13/2020", "2020-13-13", "2020-10-32",
                             "2020-10-13T25:", "2020-10-13T10:61", "2020-10-13T10:10:61",
                             "2020-10-13T10:10:40.120+45:00", "WRONG_DATE"):
                self.assertRaises(ValueError, fhir_date, "{}{}".format(op, date_str))

        # wrong operations
        self.assertRaises(ValueError, fhir_date, "wo2020-10-13T10:13:15.123+02:00")
        self.assertRaises(ValueError, fhir_date, "wlo2020-10-13T10:13:15.123+02:00")

    def test_string(self):
        test_value = "testvalue"
        for modifier in (None, ':exact', ':contains'):
            value, modifier = fhir_string(test_value, None, modifier)
            self.assertEqual(value, test_value)
            self.assertEqual(modifier, modifier)

    def test_string_with_missing_modifier(self):
        value, op, modifier = fhir_string('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_string('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_wrong_string(self):
        test_value = "testvalue"
        self.assertRaises(ValueError, fhir_string, test_value, None, 'unknown')

    def test_token(self):
        test_value = "testvalue"
        for modifier in (None, ':not', ':in', ':not-in', ':below', ':above'):
            system, code, modifier = fhir_token(test_value, None, modifier)
            self.assertEqual(system, '')
            self.assertEqual(code, test_value)
            self.assertEqual(modifier, modifier)

    def test_token_with_code_system(self):
        system_value = 'system_code'
        code_value = 'testvalue'
        for modifier in (None, ':not', ':in', ':not-in', ':below', ':above'):
            system, code, modifier = fhir_token('{}|{}'.format(system_value, code_value), None, modifier)
            self.assertEqual(system, system_value)
            self.assertEqual(code, code_value)
            self.assertEqual(modifier, modifier)

    def test_token_with_missing_modifier(self):
        value, op, modifier = fhir_token('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_token('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_wrong_token(self):
        test_value = 'testvalue'
        self.assertRaises(ValueError, fhir_string, test_value, None, 'unknown')

        test_value = 'system_code|testvalue|unkown_part'
        self.assertRaises(ValueError, fhir_token, test_value, None, ':missing')

    def test_reference(self):
        test_value = '12'  # logical id

        for modifier in [None, ':identifier', ':above', ':below']:
            value, typ, modifier = fhir_reference(test_value, None, modifier)
            self.assertEqual(typ, None)
            self.assertEqual(value, test_value)
            self.assertEqual(modifier, modifier)

        for r in RESOURCES:
            value, typ, modifier = fhir_reference('{}/{}'.format(r, test_value), None, None)
            self.assertEqual(typ, r)
            self.assertEqual(value, test_value)
            self.assertEqual(modifier, None)

            for modifier in [None, ':identifier', ':above', ':below']:
                value, typ, modifier = fhir_reference('{}/{}'.format(r, test_value), None, modifier)
                self.assertEqual(typ, r)
                self.assertEqual(value, test_value)
                self.assertEqual(modifier, modifier)

    def test_reference_with_missing_modifier(self):
        value, op, modifier = fhir_reference('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_reference('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_wrong_reference(self):
        self.assertRaises(ValueError, fhir_reference, 'Patient/12', None, 'Patient')

    def test_quantity(self):
        test_value = 5.4
        test_system = 'http://unitsofmeasure.org'
        test_code = 'mg'
        value, operation, system, code, modifier = fhir_quantity('{}|{}|{}'.format(test_value, test_system, test_code))
        self.assertEqual(operation, 'eq')
        self.assertEqual(value, test_value)
        self.assertEqual(system, test_system)
        self.assertEqual(code, test_code)

        for sp in _search_prefixes:
            value, operation, system, code, modifier = fhir_quantity('{}{}|{}|{}'.format(sp, test_value, test_system, test_code))
            self.assertEqual(operation, sp)
            self.assertEqual(value, test_value)
            self.assertEqual(system, test_system)
            self.assertEqual(code, test_code)

    def test_quantity_with_missing_modifier(self):
        value, op, modifier = fhir_quantity('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_quantity('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

    def test_quantity_error(self):
        self.assertRaises(ValueError, fhir_quantity, '5.4|http://unitsofmeasure.org')

    def test_uri(self):
        value = 'http://acme.org/fhir/ValueSet/123'
        for modifier in (None, ':above', ':below'):
            value, modifier = fhir_uri(value, None, modifier)

    def test_uri_with_missing_modifier(self):
        value, op, modifier = fhir_uri('true', None, ':missing')
        self.assertTrue(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')

        value, op, modifier = fhir_uri('false', None, ':missing')
        self.assertFalse(value)
        self.assertIsNone(op)
        self.assertEqual(modifier, ':missing')