from datetime import datetime

from fhirserver import create_app, TESTING
from fhirserver.consts import ISSUE_TYPE, ISSUE_SEVERITY
from fhirserver.dao.patient import PatientModel
from fhirserver import db
from flask_testing import TestCase


class TestPatient(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def setUp(self):
        self.settings = {
            'app_id': 'my_web_app',
            'api_base': 'http://localhost'
        }

        self.patient_data = {
            'name': [{
                'given': ['Paolino'],
                'family': 'Paperino'
            }],
            'gender': 'male',
            'birthDate': '19800320'
        }
        db.create_all()
        self.patients_data = [{
            'given_name': 'Carla',
            'family_name': 'Espinoza',
            'gender': 'f',
            'birthdate': datetime.fromisoformat('1965-12-11'),
            'address': 'Sacred Heart Street'
        }, {
            'given_name': 'Elliot',
            'family_name': 'Reed',
            'gender': 'f',
            'birthdate': datetime.fromisoformat('1970-06-18'),
            'address': 'Sacred Heart Street'
        }, {
            'given_name': 'John Arthur',
            'family_name': 'Dorian',
            'gender': 'm',
            'address': 'Sacred Heart Street'
        }, {
            'given_name': 'Percival',
            'family_name': 'Cox',
            'gender': 'm',
            'birthdate': datetime.fromisoformat('1962-07-13')
        }]
        self.add_test_patients()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_app(self):
        return create_app(TESTING)

    def add_test_patients(self):
        for patient in self.patients_data:
            pm = PatientModel(**patient)
            db.session.add(pm)
            patient['id'] = pm.id

        db.session.commit()

    def test_correct_creation(self):
        res = self.client.post('/Patient',
                               json=self.patient_data,
                               headers={'Accept': 'application/fhir+json'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.headers['Content-Type'], 'application/fhir+json')
        self.assertEqual(res.headers['Location'], '{}/Patient/{}'.format(self.settings['api_base'], res.json['id']))

    def test_wrong_accept_header(self):
        res = self.client.post('/Patient',
                               json=self.patient_data,
                               headers={'Accept': 'application/fhir+xml'})
        self.assertEqual(res.status_code, 400)
        op_outcome_issues = [{
            'code': ISSUE_TYPE.INVALID,
            'severity': ISSUE_SEVERITY.FATAL,
            'expression': ['Accept']
        }]
        self.assertEqual(res.json['issue'], op_outcome_issues)

    def test_missing_accept_header(self):
        res = self.client.post('/Patient',
                               json=self.patient_data)
        self.assertEqual(res.status_code, 400)
        op_outcome_issues = [{
            'code': ISSUE_TYPE.REQUIRED,
            'severity': ISSUE_SEVERITY.FATAL,
            'expression': ['Accept']
        }]
        self.assertEqual(res.json['issue'], op_outcome_issues)

    def test_invalid_input_data(self):
        patient_data = {
            'name': {
                'given': ['Paolino'],
                'family': 'Paperino'
            },
            'gender': 'male',
            'birthDate': '19800320'
        }
        res = self.client.post('/Patient',
                               json=patient_data,
                               headers={'Accept': 'application/fhir+json'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json['resourceType'], 'OperationOutcome')
        op_outcome_issues = [{
            'code': ISSUE_TYPE.INVALID,
            'severity': ISSUE_SEVERITY.FATAL,
            'expression': ['name']
        }]
        self.assertEqual(res.json['issue'], op_outcome_issues)

    def test_get_patient_by_id_not_found(self):
        res = self.client.get('/Patient/fake_id', headers={'Accept': 'application/fhir+json'})
        self.assert404(res)
        self.assertEqual(res.json['resourceType'], 'OperationOutcome')
        op_outcome_issues = [{
            'code': ISSUE_TYPE.NOT_FOUND,
            'severity': ISSUE_SEVERITY.ERROR,
        }]
        self.assertEqual(res.json['issue'], op_outcome_issues)

    def test_get_patient_by_id(self):
        res = self.client.get('/Patient/{}'.format(self.patients_data[0]['id']),
                              headers={'Accept': 'application/fhir+json'})
        self.assert200(res)
        self.assertEqual(res.json['resourceType'], 'Patient')
        self.assertEqual(res.json, PatientModel(**self.patients_data[0]).to_fhir_res().as_json())

    def test_get_all_patients(self):
        res = self.client.get('/Patient/', headers={'Accept': 'application/fhir+json'})
        self.assert200(res)
        self.assertEqual(res.json['resourceType'], 'Bundle')
        self.assertEqual(res.json['type'], 'searchset')
        for index, patient in enumerate(res.json['entry']):
            self.assertEqual(patient['fullUrl'],
                             '{}/Patient/{}'.format(self.settings['api_base'], self.patients_data[index]['id']))
            self.assertEqual(patient['resource'], PatientModel(**self.patients_data[index]).to_fhir_res().as_json())

    def _search_patient(self, queries):
        for query in queries:
            query_string = "&".join(["{}={}".format(param_name, param_value)
                                     for param_name, param_value in query.items() if param_name != 'expected'])

            res = self.client.get('/Patient?{}'.format(query_string), headers={'Accept': 'application/fhir+json'})
            self.assert200(res)
            self.assertEqual(res.json['resourceType'], 'Bundle')
            self.assertEqual(res.json['type'], 'searchset')
            self.assertEqual(res.json['total'], query['expected'])
            self.assertEqual(len(res.json['entry']), query['expected'])

    def test_search_by_string(self):
        queries = [
            # {'_id': self.patients_data[0]['id'], 'expected': 1},
            {'address': self.patients_data[0]['address'], 'expected': 3},
            {'address:exact': self.patients_data[0]['address'], 'expected': 3},
            {'address:contains': self.patients_data[0]['address'][4:10], 'expected': 3},
            {'address:missing': 'true', 'expected': 1},
            {'address:missing': 'false', 'expected': 3}
        ]
        self._search_patient(queries)

    def test_search_by_date(self):
        queries = [
            {'birthdate:missing': 'true', 'expected': 1},
            {'birthdate': 'eq{}'.format(self.patients_data[0]['birthdate'].date().isoformat()), 'expected': 1},
            {'birthdate': 'eq{}T15:00:31'.format(self.patients_data[0]['birthdate'].date().isoformat()), 'expected': 1},
            {'birthdate': 'eq1850-08-23T15:00:31', 'expected': 0},
            {'birthdate': 'ne1850-08-23T15:00:31', 'expected': 3},
            {'birthdate': 'ne{}'.format(self.patients_data[0]['birthdate'].date().isoformat()), 'expected': 2},
            {'birthdate': 'lt1966', 'expected': 2},
            {'birthdate': 'lt1965-12-11T11:00', 'expected': 2},
            {'birthdate': 'gt1966', 'expected': 1},
            {'birthdate': 'gt1965-12-11T11:00', 'expected': 2},
            {'birthdate': 'le1965-12-11', 'expected': 2},
            {'birthdate': 'ge1965-12-11', 'expected': 2},
            {'birthdate': 'sa1966', 'expected': 1},
            {'birthdate': 'sa1965-12-11T11:00', 'expected': 2},
            {'birthdate': 'eb1966', 'expected': 2},
            {'birthdate': 'eb1965-12-11T11:00', 'expected': 2},
            {'birthdate': 'ap1965-12-10', 'expected': 1},
            {'birthdate': 'ap1965-12-12', 'expected': 1},
            {'birthdate': 'ap1965-12-09', 'expected': 0},
            {'birthdate': 'ap1965-12-13', 'expected': 0},
        ]
        self._search_patient(queries)

    def test_search_wrong_date_format(self):
        res = self.client.get('/Patient?birthdate=19650606', headers={'Accept': 'application/fhir+json'})
        self.assert400(res)
        # self.assertEqual(res.json['resourceType'], 'OperationOutcome')
        # op_outcome_issues = [{
        #     'code': ISSUE_TYPE.NOT_FOUND,
        #     'severity': ISSUE_SEVERITY.ERROR,
        # }]
        # self.assertEqual(res.json['issue'], op_outcome_issues)

    # def test_search_patients_no_entry_found(self):
    #     res = self.client.get('/Patient?_id=unknown', headers={'Accept': 'application/fhir+json'})
    #     self.assert200(res)
    #     self.assertEqual(res.json['resourceType'], 'Bundle')
    #     self.assertEqual(res.json['type'], 'searchset')
    #     self.assertEqual(res.json['total'], 0)
    #     self.assertEqual(res.json['entry'], [])

