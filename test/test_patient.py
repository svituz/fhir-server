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
            'birth_date': datetime.fromisoformat('1965-12-11')
        }, {
            'given_name': 'Elliot',
            'family_name': 'Reed',
            'gender': 'f',
            'birth_date': datetime.fromisoformat('1970-06-18')
        }, {
            'given_name': 'John Arthur',
            'family_name': 'Dorian',
            'gender': 'm',
            'birth_date': datetime.fromisoformat('1970-10-05')
        }, {
            'given_name': 'Percival',
            'family_name': 'Cox',
            'gender': 'm',
            'birth_date': datetime.fromisoformat('1962-07-13')
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

    # def test_search_patients(self):
    #     queries = [
    #         {'_id': self.patients_data[0]['id'], 'expected': 1},
    #         # {'id': self.patients_data[0]['id'], 'expected': 1},
    #         {'gender': 'f', 'expected': 2},
    #         {'active': True, 'expected': 4},
    #         {'birthdate': 'eq{}'.format(self.patients_data[0]['birth_date'].date().isoformat()), 'expected': 1},
    #     ]
    #     for query in queries:
    #         query_string = "&".join(["{}={}".format(param_name, param_value)
    #                                  for param_name, param_value in query.items() if param_name != 'expected'])
    #         res = self.client.get('/Patient?{}'.format(query_string), headers={'Accept': 'application/fhir+json'})
    #         self.assert200(res)
    #         self.assertEqual(res.json['resourceType'], 'Bundle')
    #         self.assertEqual(res.json['type'], 'searchset')
    #         self.assertEqual(res.json['total'], len(res.json['entry']), query['expected'])

    def test_search_wrong_date_format(self):
        res = self.client.get('/Patient?birthdate=19650606', headers={'Accept': 'application/fhir+json'})
        self.assert400(res)
        # self.assertEqual(res.json['resourceType'], 'OperationOutcome')
        # op_outcome_issues = [{
        #     'code': ISSUE_TYPE.NOT_FOUND,
        #     'severity': ISSUE_SEVERITY.ERROR,
        # }]
        # self.assertEqual(res.json['issue'], op_outcome_issues)

    def test_search_patients_no_entry_found(self):
        res = self.client.get('/Patient?_id=unknown', headers={'Accept': 'application/fhir+json'})
        self.assert200(res)
        self.assertEqual(res.json['resourceType'], 'Bundle')
        self.assertEqual(res.json['type'], 'searchset')
        self.assertEqual(res.json['total'], 0)
        self.assertEqual(res.json['entry'], [])

