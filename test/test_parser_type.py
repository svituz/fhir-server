from unittest import TestCase

from dateutil.parser import isoparse

from fhirserver.parser_types import FHIRNumber, FHIRDate, FHIRString, FHIRToken, FHIRReference, FHIRQuantity, FHIRUri
from fhirserver.resources import RESOURCES

_search_prefixes = ('eq', 'ne', 'gt', 'lt', 'ge', 'le', 'gt', 'sa', 'eb', 'ap')


class TestFHIRSearchTypes(TestCase):

    def test_number_with_int_string(self):
        fn = FHIRNumber("100")
        self.assertEqual(fn.value, 100)
        self.assertEqual(fn.operation, 'eq')
        self.assertIsNone(fn.modifier)

    def test_number_with_missing_modifier(self):
        fn = FHIRNumber('true', None, ':missing=')
        self.assertTrue(fn.value)
        self.assertIsNone(fn.operation)
        self.assertEqual(fn.modifier, ':missing')

        fn = FHIRNumber('false', None, ':missing=')
        self.assertFalse(fn.value)
        self.assertIsNone(fn.operation)
        self.assertEqual(fn.modifier, ':missing')

    def test_number_with_float_string(self):
        fn = FHIRNumber("100.00")
        self.assertEqual(fn.value, 100.00)
        self.assertEqual(fn.operation, 'eq')
        self.assertIsNone(fn.modifier)

        fn = FHIRNumber("1e2")
        self.assertEqual(fn.value, 100.00)
        self.assertEqual(fn.operation, 'eq')
        self.assertIsNone(fn.modifier)

    def test_number_with_operator(self):
        for operation in ('lt', 'le', 'gt', 'ge', 'ne'):
            fn = FHIRNumber("{}100".format(operation))
            self.assertEqual(fn.operation, operation)
            self.assertEqual(fn.value, 100)
            self.assertIsNone(fn.modifier)

            fn = FHIRNumber("{}100.00".format(operation))
            self.assertEqual(fn.operation, operation)
            self.assertEqual(fn.value, 100.00)
            self.assertIsNone(fn.modifier)

    def test_wrong_number(self):
        self.assertRaises(ValueError, FHIRNumber, "st100", None, None)
        self.assertRaises(ValueError, FHIRNumber, "100,00", None, None)
        self.assertRaises(ValueError, FHIRNumber, "notanumber", None, None)
        self.assertRaises(ValueError, FHIRNumber, '100', None, ':missing=')

    def test_date(self):
        for op in _search_prefixes:
            for date_str in ("2020", "2020-10", "2020-10-13", "2020-10-13T10", "2020-10-13T10:13",
                             "2020-10-13T10:13:15", "2020-10-13T10:13:15.123", "2020-10-13T10:13:15.123+02:00"):
                fd = FHIRDate("{}{}".format(op, date_str))
                self.assertEqual(fd.operation, op)
                self.assertEqual(fd.value, isoparse(date_str))

    def test_date_with_missing_modifier(self):
        fd = FHIRDate('true', None, ':missing=')
        self.assertTrue(fd.value)
        self.assertIsNone(fd.operation)
        self.assertEqual(fd.modifier, ':missing')

        fd = FHIRDate('false', None, ':missing=')
        self.assertFalse(fd.value)
        self.assertIsNone(fd.operation)
        self.assertEqual(fd.modifier, ':missing')

    def test_wrong_date(self):
        # wrong date values
        for op in _search_prefixes:
            for date_str in ("2020-", "10-13-2020", "10/13/2020", "2020-13-13", "2020-10-32",
                             "2020-10-13T25:", "2020-10-13T10:61", "2020-10-13T10:10:61",
                             "2020-10-13T10:10:40.120+45:00", "WRONG_DATE"):
                self.assertRaises(ValueError, FHIRDate, "{}{}".format(op, date_str))

        # wrong operations
        self.assertRaises(ValueError, FHIRDate, "wo2020-10-13T10:13:15.123+02:00")
        self.assertRaises(ValueError, FHIRDate, "wlo2020-10-13T10:13:15.123+02:00")

    def test_string(self):
        test_value = "testvalue"
        for operator in (':exact=', ':contains='):
            fs = FHIRString(test_value, None, operator)
            self.assertEqual(fs.value, test_value)
            self.assertEqual(fs.modifier, operator.replace('=', ''))

    def test_string_with_missing_modifier(self):
        fs = FHIRString('true', None, ':missing=')
        self.assertTrue(fs.value)
        self.assertEqual(fs.modifier, ':missing')

        fs = FHIRString('false', None, ':missing=')
        self.assertFalse(fs.value)
        self.assertEqual(fs.modifier, ':missing')

    def test_wrong_string(self):
        """
        Tests error in case of unknown modifier
        """
        test_value = "testvalue"
        self.assertRaises(ValueError, FHIRString, test_value, None, 'unknown')

    def test_token(self):
        test_value = "testvalue"
        for operator in (':not=', ':in=', ':not-in=', ':below=', ':above='):
            ft = FHIRToken(test_value, None, operator)
            self.assertEqual(ft.system, '')
            self.assertEqual(ft.value, test_value)
            self.assertEqual(ft.modifier, operator.replace('=', ''))

    def test_token_with_code_system(self):
        system_value = 'system_code'
        code_value = 'testvalue'
        for operator in (':not=', ':in=', ':not-in=', ':below=', ':above='):
            ft = FHIRToken('{}|{}'.format(system_value, code_value), None, operator)
            self.assertEqual(ft.system, system_value)
            self.assertEqual(ft.value, code_value)
            self.assertEqual(ft.modifier, operator.replace('=', ''))

    def test_token_with_missing_modifier(self):
        ft = FHIRToken('true', None, ':missing=')
        self.assertTrue(ft.value)
        self.assertIsNone(ft.system)
        self.assertEqual(ft.modifier, ':missing')

        ft = FHIRToken('false', None, ':missing=')
        self.assertFalse(ft.value)
        self.assertIsNone(ft.system)
        self.assertEqual(ft.modifier, ':missing')

    def test_wrong_token(self):
        test_value = 'testvalue'
        self.assertRaises(ValueError, FHIRString, test_value, None, 'unknown')

        test_value = 'system_code|testvalue|unkown_part'
        self.assertRaises(ValueError, FHIRToken, test_value, None, ':missing=')

    def test_reference(self):
        test_value = '12'  # logical id

        for operator in (':identifier=', ':above=', ':below='):
            fr = FHIRReference(test_value, None, operator)
            self.assertEqual(fr.type, None)
            self.assertEqual(fr.value, test_value)
            self.assertEqual(fr.modifier, operator.replace('=', ''))

        for r in RESOURCES:
            fr = FHIRReference('{}/{}'.format(r, test_value), None, None)
            self.assertEqual(fr.type, r)
            self.assertEqual(fr.value, test_value)
            self.assertEqual(fr.modifier, None)

            for operator in (':identifier=', ':above=', ':below='):
                fr = FHIRReference('{}/{}'.format(r, test_value), None, operator)
                self.assertEqual(fr.type, r)
                self.assertEqual(fr.value, test_value)
                self.assertEqual(fr.modifier, operator.replace('=', ''))

    def test_reference_with_missing_modifier(self):
        fr = FHIRReference('true', None, ':missing=')
        self.assertTrue(fr.value)
        self.assertIsNone(fr.type)
        self.assertEqual(fr.modifier, ':missing')

        fr = FHIRReference('false', None, ':missing=')
        self.assertFalse(fr.value)
        self.assertIsNone(fr.type)
        self.assertEqual(fr.modifier, ':missing')

    def test_wrong_reference(self):
        self.assertRaises(ValueError, FHIRReference, 'Patient/12', None, 'Patient')

    def test_quantity(self):
        test_value = 5.4
        test_system = 'http://unitsofmeasure.org'
        test_code = 'mg'
        fq = FHIRQuantity('{}|{}|{}'.format(test_value, test_system, test_code))
        self.assertEqual(fq.operation, 'eq')
        self.assertEqual(fq.value, test_value)
        self.assertEqual(fq.system, test_system)
        self.assertEqual(fq.code, test_code)
        self.assertIsNone(fq.modifier)

        for sp in _search_prefixes:
            fq = FHIRQuantity('{}{}|{}|{}'.format(sp, test_value, test_system, test_code))
            self.assertEqual(fq.operation, sp)
            self.assertEqual(fq.value, test_value)
            self.assertEqual(fq.system, test_system)
            self.assertEqual(fq.code, test_code)
            self.assertIsNone(fq.modifier)

    def test_quantity_with_missing_modifier(self):
        fq = FHIRQuantity('true', None, ':missing=')
        self.assertTrue(fq.value)
        self.assertIsNone(fq.operation)
        self.assertIsNone(fq.system)
        self.assertIsNone(fq.code)
        self.assertEqual(fq.modifier, ':missing')

        fq = FHIRQuantity('false', None, ':missing=')
        self.assertFalse(fq.value)
        self.assertIsNone(fq.operation)
        self.assertIsNone(fq.system)
        self.assertIsNone(fq.code)
        self.assertEqual(fq.modifier, ':missing')

    def test_quantity_error(self):
        self.assertRaises(ValueError, FHIRQuantity, '5.4|http://unitsofmeasure.org')

    def test_uri(self):
        value = 'http://acme.org/fhir/ValueSet/123'
        for operator in (':above=', ':below='):
            fu = FHIRUri(value, None, operator)
            self.assertEqual(fu.value, value)
            self.assertEqual(fu.modifier, operator.replace('=', ''))

    def test_uri_with_missing_modifier(self):
        fu = FHIRUri('true', None, ':missing=')
        self.assertTrue(fu.value)
        self.assertEqual(fu.modifier, ':missing')

        fu = FHIRUri('false', None, ':missing=')
        self.assertFalse(fu.value)
        self.assertEqual(fu.modifier, ':missing')