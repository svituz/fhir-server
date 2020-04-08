from flask import request
from flask_restful import Resource

from fhirclient.models.fhirabstractbase import FHIRValidationError
from fhirclient.models.patient import Patient as FHIRPatient
from fhirserver import db
from fhirserver.exceptions import InvalidBodyException, NotFoundException
from fhirserver.dao.patient import PatientDAO
from fhirserver.parser_types import query_argument_type_factory, FHIRSearchTypes

patients_db = {}


def _get_patient(patient_id):
    p = FHIRPatient()
    p.id = str(patient_id)
    return p


class PatientResource(Resource):
    """
    Rest resource for Patient
    """
    def get(self, patient_id):
        patient = PatientDAO.get(patient_id)
        if patient is None:
            raise NotFoundException
        else:
            return patient.as_json(), 200,


class PatientListResource(Resource):

    def get_search_parameters(self):
        arguments = [
            query_argument_type_factory('active', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('address', FHIRSearchTypes.STRING),
            query_argument_type_factory('address-city', FHIRSearchTypes.STRING),
            query_argument_type_factory('address-countr', FHIRSearchTypes.STRING),
            query_argument_type_factory('address-postalcode', FHIRSearchTypes.STRING),
            query_argument_type_factory('address-state', FHIRSearchTypes.STRING),
            query_argument_type_factory('address-use', FHIRSearchTypes.STRING),
            query_argument_type_factory('birthdate', FHIRSearchTypes.DATE),
            query_argument_type_factory('death-date', FHIRSearchTypes.DATE),
            query_argument_type_factory('deceased', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('email', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('family', FHIRSearchTypes.STRING),
            query_argument_type_factory('gender', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('general-practitioner', FHIRSearchTypes.REFERENCE),
            query_argument_type_factory('given', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('identifier', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('language', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('link', FHIRSearchTypes.REFERENCE),
            query_argument_type_factory('name', FHIRSearchTypes.STRING),
            query_argument_type_factory('organization', FHIRSearchTypes.REFERENCE),
            query_argument_type_factory('phone', FHIRSearchTypes.TOKEN),
            query_argument_type_factory('phonetic', FHIRSearchTypes.STRING),
            query_argument_type_factory('telecom', FHIRSearchTypes.TOKEN),
        ]
        return arguments

    def get(self, arguments):
        patients = PatientDAO.search(**arguments)
        return patients

    def post(self):
        data = request.json
        try:
            patient = FHIRPatient(data)
        except FHIRValidationError as e:
            raise InvalidBodyException(e)
        else:
            res = PatientDAO.create(patient)
            return res
