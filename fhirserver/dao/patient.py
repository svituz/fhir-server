import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, Boolean

from fhirclient.models.patient import Patient
from fhirserver import db
from fhirserver.parser_types import FHIRString, FHIRToken


class PatientModel(db.Model):
    __tablename__ = 'patients'
    id = Column(String(32), primary_key=True)
    identifier = Column(String(32), nullable=True)
    active = Column(Boolean(), default=True)
    given_name = Column(String(50), nullable=None)
    family_name = Column(String(120), nullable=None)
    gender = Column(String(1), nullable=None)
    birth_date = Column(Date())

    def __init__(self, id=None, identifier=None, given_name=None, family_name=None, gender=None, birth_date=None):
        self.id = uuid.uuid4().hex if id is None else id
        self.active = True
        self.given_name = given_name
        self.family_name = family_name
        self.gender = gender
        self.birth_date = birth_date.date()  # gets only the date from birth_date if it's a datetime

    @classmethod
    def from_fhir_res(cls, patient):
        given_name = ' '.join(given.value for given in patient.name[0].given)
        family_name = patient.name[0].family.value
        gender = {'male': 'm', 'female': 'f', 'unknown': 'u', 'other': 'o'}[patient.gender.value.lower()]
        birth_date = datetime.fromisoformat(patient.birthDate.isostring)
        return PatientModel(given_name=given_name, family_name=family_name, gender=gender, birth_date=birth_date)

    def to_fhir_res(self):
        data = {
            'id': self.id,
            'identifier': [{
                'value': self.identifier
            }],
            'name': [{
                'given': self.given_name.split(' '),
                'family': self.family_name
            }],
            'gender': {'m': 'male', 'f': 'female', 'u': 'unknown', 'o': 'other'}[self.gender],
            'birthDate': self.birth_date.isoformat()
        }
        return Patient(data)

    def __repr__(self):
        return f'<Patient {self.give_name} {self.family_name}>'


class PatientDAO(object):

    @classmethod
    def get(cls, patient_id):
        patient = PatientModel.query.get(patient_id)
        if patient is not None:
            return patient.to_fhir_res()
        return None

    @classmethod
    def search(cls, **query_args):
        filters = []
        for name, search_object in query_args.items():
            if search_object is not None:
                if isinstance(search_object, FHIRString):
                    filters.append(getattr(PatientModel, name) == search_object.value)
                elif isinstance(search_object, FHIRToken):
                    if search_object.modifier == ':not=':
                        filters.append(getattr(PatientModel, name) != search_object.value)
                    else:
                        filters.append(getattr(PatientModel, name) == search_object.value)

        return [patient.to_fhir_res() for patient in PatientModel.query.filter(*filters).all()]

    @classmethod
    def create(cls, item):
        patient = PatientModel.from_fhir_res(item)
        db.session.add(patient)
        db.session.commit()
        return patient.to_fhir_res()
