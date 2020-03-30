from fhirclient.models.fhirabstractbase import FHIRValidationError
from fhirclient.models.operationoutcome import OperationOutcome, OperationOutcomeIssue
from flask import Flask, make_response
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound

from config import DevelopConfig, TestConfig
from fhirserver.consts import ISSUE_SEVERITY, ISSUE_TYPE
from fhirserver.exceptions import FHIRServerException

db = SQLAlchemy()

from fhirserver.resources.router import InvalidHeaderException, BaseListResource, BaseResource

DEVELOPMENT = 'DEV'
TESTING = 'TEST'
PRODUCTION = 'PROD'


def create_app(config):
    assert config in (DEVELOPMENT, TESTING, PRODUCTION)
    from fhirserver.resources.patient import PatientResource, PatientListResource

    app = Flask('FHIR Server')
    conf = DevelopConfig
    if config == DEVELOPMENT:
        conf = DevelopConfig
    elif config == TESTING:
        conf = TestConfig

    app.config.from_object(conf)

    api = Api(app)
    db.init_app(app)

    with app.app_context():
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            db.session.remove()

        @api.representation('application/fhir+json')
        def output_json(data, code, headers=None):
            resp = make_response(data, code)
            resp.headers.extend(headers or {})
            return resp

        @app.errorhandler(FHIRServerException)
        def error_handler(exc):
            op_outcome = OperationOutcome()
            issues = []
            for error in exc.errors:
                issue = OperationOutcomeIssue()
                issue.severity = error.severity
                if error.path is not None:
                    issue.expression = [error.path]
                issue.code = error.code
                issues.append(issue)
            op_outcome.issue = issues
            return op_outcome.as_json(), exc.http_code

        db.create_all()

        # api.add_resource(PatientResource, '/Patient/<string:patient_id>', '/Patient/<string:patient_id>/')
        # api.add_resource(PatientListResource, '/Patient', '/Patient/')
        api.add_resource(BaseListResource, '/<string:resource_type>', '/<string:resource_type>/')
        api.add_resource(BaseResource, '/<string:resource_type>/<string:resource_id>',
                         '/<string:resource_type>/<string:resource_id>/')
        return app
