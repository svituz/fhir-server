from flask import request
from flask_restful import reqparse, Resource
from werkzeug.exceptions import HTTPException

from fhirclient.models.bundle import Bundle, BundleEntry
from fhirserver import resources
from fhirserver.exceptions import InvalidHeaderException, NotFoundException, InvalidQueryParameterException
from fhirserver.parser_types import FHIRSearchTypes, \
    query_argument_type_factory


def _get_resource(resource_cls_name):
    try:
        resource = getattr(resources, resource_cls_name)
    except AttributeError:
        raise NotFoundException

    return resource()


class BaseResource(Resource):
    def get(self, resource_type, resource_id):
        resource = _get_resource('{}Resource'.format(resource_type))
        return resource.get(resource_id)


class BaseListResource(Resource):

    def __init__(self):
        self.base_headers = {
            'Content-type': 'application/fhir+json'
        }

    @staticmethod
    def _parse_headers():
        """
        Check that Accept exists and the only accepted value is application/fhir+json
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('Accept', type=str, location='headers',
                            choices=('application/fhir+json',), required=True)
        try:
            args = parser.parse_args()
        except HTTPException as e:
            raise InvalidHeaderException(e.code, e.data)

        return {name: value for name, value in args.items() if value is not None}

    @staticmethod
    def _parse_search_parameters(resource_arguments):
        """
        Parse
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument(query_argument_type_factory('_content', FHIRSearchTypes.STRING, 'content'))
        parser.add_argument(query_argument_type_factory('_id', FHIRSearchTypes.TOKEN, 'id'))
        parser.add_argument(query_argument_type_factory('_lastUpdated', FHIRSearchTypes.DATE, 'lastUpdated'))
        parser.add_argument(query_argument_type_factory('_profile', FHIRSearchTypes.URI, 'profile'))
        parser.add_argument(query_argument_type_factory('_query', FHIRSearchTypes.TOKEN, 'query'))
        parser.add_argument(query_argument_type_factory('_security', FHIRSearchTypes.TOKEN, 'security'))
        parser.add_argument(query_argument_type_factory('_source', FHIRSearchTypes.URI, 'source'))
        parser.add_argument(query_argument_type_factory('_tag', FHIRSearchTypes.TOKEN, 'tag'))

        for argument in resource_arguments:
            parser.add_argument(argument)

        try:
            args = parser.parse_args()
        except HTTPException as e:
            raise InvalidQueryParameterException(e.code, e.data)
        return {name: value for name, value in args.items() if value is not None}

    @staticmethod
    def _create_bundle_response(entries):
        bundle = Bundle()
        bundle.type = 'searchset'
        bundle.entry = []
        bundle.total = len(entries)
        for item in entries:
            entry = BundleEntry()
            entry.fullUrl = '{}{}'.format(request.base_url, item.id.value)
            entry.resource = item
            bundle.entry.append(entry)
        return bundle

    def post(self, resource_type):
        resource = _get_resource('{}ListResource'.format(resource_type))

        self._parse_headers()

        item = resource.post()

        headers = self.base_headers.copy()
        headers.update({
            'Location': '{}/{}'.format(request.base_url, item.id.value),
        })
        return item.as_json(), 201, headers

    def get(self, resource_type):
        resource = _get_resource('{}ListResource'.format(resource_type))

        arguments = resource.get_search_parameters()

        parsed_arguments = self._parse_search_parameters(arguments)

        items = resource.get(parsed_arguments)

        bundle = self._create_bundle_response(items)
        return bundle.as_json(), 200, self.base_headers



