import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, Boolean, DateTime

from fhirclient.models.patient import Patient
from fhirserver import db


class PatientModel(db.Model):
    __tablename__ = 'patients'
    id = Column(String(32), primary_key=True)
    identifier = Column(String(32), nullable=True)
    active = Column(Boolean(), default=True)
    given_name = Column(String(50), nullable=None)
    family_name = Column(String(120), nullable=None)
    gender = Column(String(1), nullable=None)
    address = Column(String(100), nullable=True)
    birthdate = Column(Date())

    def __init__(self, id=None, identifier=None, given_name=None, family_name=None,
                 gender=None, birthdate=None, address=None):
        self.id = uuid.uuid4().hex if id is None else id
        self.active = True
        self.given_name = given_name
        self.family_name = family_name
        self.gender = gender
        self.address = address
        # gets only the date from birthdate if it's a datetime
        self.birthdate = birthdate.date() if birthdate is not None else None

    @classmethod
    def from_fhir_res(cls, patient):
        given_name = ' '.join(given.value for given in patient.name[0].given)
        family_name = patient.name[0].family.value
        gender = {'male': 'm', 'female': 'f', 'unknown': 'u', 'other': 'o'}[patient.gender.value.lower()]
        birthdate = datetime.fromisoformat(patient.birthDate.isostring)
        address = patient.address[0].text.value if patient.address is not None else None
        return PatientModel(given_name=given_name, family_name=family_name, gender=gender, birthdate=birthdate,
                            address=address)

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
            'birthDate': self.birthdate.isoformat() if self.birthdate is not None else None,
            'address': [{
                'text': self.address
            }]
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
        for name, qp in query_args.items():
            if qp is not None:
                condition = qp.get_query_condition(getattr(PatientModel, name))
                filters.append(condition)
        return [patient.to_fhir_res() for patient in PatientModel.query.filter(*filters).all()]

    @classmethod
    def create(cls, item):
        patient = PatientModel.from_fhir_res(item)
        db.session.add(patient)
        db.session.commit()
        return patient.to_fhir_res()
