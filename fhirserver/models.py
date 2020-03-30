import uuid
from datetime import date, datetime

from sqlalchemy import Column, String, Date, Boolean
from fhirclient.models.patient import Patient

from . import db


class PatientModel(db.Model):
    __tablename__ = 'patients'
    identifier = Column(String(32), primary_key=True)
    active = Column(Boolean(), default=True)
    given_name = Column(String(50), nullable=None)
    family_name = Column(String(120), nullable=None)
    gender = Column(String(1), nullable=None)
    birth_date = Column(Date())

    def __init__(self, identifier=None, given_name=None, family_name=None, gender=None, birth_date=None):
        self.identifier = uuid.uuid4().hex if identifier is None else identifier
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
