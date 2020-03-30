from flask import request
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from werkzeug.exceptions import HTTPException

from fhirclient.models.fhirabstractbase import FHIRValidationError
from fhirclient.models.patient import Patient
from fhirserver import db
from fhirserver.exceptions import InvalidBodyException, NotFoundException, InvalidQueryParameterException
from fhirserver.models import PatientModel
from fhirserver.parser_types import fhir_date, fhir_token

patients_db = {}


def _get_patient(patient_id):
    p = Patient()
    p.id = str(patient_id)
    return p


class PatientResource(Resource):
    """
    Rest resource for Patient
    """
    def get(self, patient_id):
        patient = PatientModel.query.filter_by(identifier=patient_id).first()
        if patient is None:
            print("search failed")
            raise NotFoundException
        else:
            return patient.to_fhir_res().as_json(), 200,


class PatientListResource(Resource):
    def get(self):
        qp_parser = RequestParser()
        operators = ['=', ':text=', ':not=', ':above=', ':below=', ':in=', ':not-in=', ':of-type=']
        qp_parser.add_argument('_id', dest='identifier', location='args', type=fhir_token, operators=operators)
        qp_parser.add_argument('gender', type=str, help='The gender of the patient(s)',
                               choices=('f', 'm'), location='args')
        qp_parser.add_argument('active', type=bool, location='args')
        qp_parser.add_argument('birthdate', dest='birth_date', type=fhir_date, location='args')
        # qp_parser.add_argument('identifier', location='args', type=fhir_token)

        try:
            args = qp_parser.parse_args()
        except HTTPException as e:
            raise InvalidQueryParameterException(e.code, e.data)

        filters = []

        for name, value in args.items():
            if value is not None:
                if isinstance(value, tuple):
                    if len(value) == 2:
                        operation, value = value
                        if isinstance(value, tuple):
                            value = value[1]
                        filters.append(operation(getattr(PatientModel, name), value))
                    else:
                        filters.append(getattr(PatientModel, name) == value)
                else:
                    filters.append(getattr(PatientModel, name) == value)
        patients = PatientModel.query.filter(*filters).all()
        return [patient.to_fhir_res() for patient in patients]

    def post(self):
        data = request.json
        try:
            patient = Patient(data)
        except FHIRValidationError as e:
            raise InvalidBodyException(e)
        else:
            db_patient = PatientModel.from_fhir_res(patient)
            db.session.add(db_patient)
            db.session.commit()

        return db_patient.to_fhir_res()
