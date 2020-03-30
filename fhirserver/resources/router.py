from flask import request
from flask_restful import reqparse, Resource
from werkzeug.exceptions import HTTPException

from fhirclient.models.bundle import Bundle, BundleEntry
from fhirserver import resources
from fhirserver.exceptions import InvalidHeaderException, NotFoundException


# class TokenArgument(Argument):
#
#     def __init__(self, name, default=None, dest=None, required=False,
#                  ignore=False, location=('json', 'values',),
#                  choices=(), action='store', help=None, operators=('=',),
#                  case_sensitive=True, store_missing=True, trim=False,
#                  nullable=True):
#
#         self.modifiers = ['', ':text', ':not', ':above', ':below', ':in', ':not-in', ':of-type']
#         self.operators = ['=', ':text=', ':not=', ':above=', ':below=', ':in=', ':not-in=', ':of-type=']
#
#         super(TokenArgument, self).__init__(name, default, dest, required, ignore,
#                                             fhir_token, location, choices, action, help,
#                                             operators, case_sensitive, store_missing, trim,
#                                             nullable)
#
#     def parse(self, request, bundle_errors=False):
#         """Parses argument value(s) from the request, converting according to
#         the argument's type.
#
#         :param request: The flask request object to parse arguments from
#         :param bundle_errors: Do not abort when first error occurs, return a
#             dict with the name of the argument and the error message to be
#             bundled
#         """
#         source = self.source(request)
#         # print(source)
#         results = []
#
#         # Sentinels
#         _not_found = False
#         _found = True
#
#         for operator in self.operators:
#             for modifier in self.modifiers:
#                 name = "{}{}{}".format(self.name, modifier, operator.replace("=", "", 1))
#                 if name in source:
#                     # Account for MultiDict and regular dict
#                     if hasattr(source, "getlist"):
#                         values = source.getlist(name)
#                     else:
#                         values = source.get(name)
#                         if not (isinstance(values, MutableSequence) and self.action == 'append'):
#                             values = [values]
#
#                     for value in values:
#                         if hasattr(value, "strip") and self.trim:
#                             value = value.strip()
#                         if hasattr(value, "lower") and not self.case_sensitive:
#                             value = value.lower()
#
#                             if hasattr(self.choices, "__iter__"):
#                                 self.choices = [choice.lower()
#                                                 for choice in self.choices]
#
#                         try:
#                             value = self.convert(value, operator)
#                         except Exception as error:
#                             if self.ignore:
#                                 continue
#                             return self.handle_validation_error(error, bundle_errors)
#
#                         if self.choices and value not in self.choices:
#                             if current_app.config.get("BUNDLE_ERRORS", False) or bundle_errors:
#                                 return self.handle_validation_error(
#                                     ValueError(u"{0} is not a valid choice".format(
#                                         value)), bundle_errors)
#                             self.handle_validation_error(
#                                     ValueError(u"{0} is not a valid choice".format(
#                                         value)), bundle_errors)
#
#                         if name in request.unparsed_arguments:
#                             request.unparsed_arguments.pop(name)
#                         results.append(value)
#
#         if not results and self.required:
#             if isinstance(self.location, six.string_types):
#                 error_msg = u"Missing required parameter in {0}".format(
#                     _friendly_location.get(self.location, self.location)
#                 )
#             else:
#                 friendly_locations = [_friendly_location.get(loc, loc)
#                                       for loc in self.location]
#                 error_msg = u"Missing required parameter in {0}".format(
#                     ' or '.join(friendly_locations)
#                 )
#             if current_app.config.get("BUNDLE_ERRORS", False) or bundle_errors:
#                 return self.handle_validation_error(ValueError(error_msg), bundle_errors)
#             self.handle_validation_error(ValueError(error_msg), bundle_errors)
#
#         if not results:
#             if callable(self.default):
#                 return self.default(), _not_found
#             else:
#                 return self.default, _not_found
#
#         if self.action == 'append':
#             return results, _found
#
#         if self.action == 'store' or len(results) == 1:
#             return results[0], _found
#         return results, _found


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
    def validate_headers():
        """
        Check that Accept exists and the only accepted value is application/fhir+json
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('Accept', type=str, location='headers',
                            choices=('application/fhir+json',), required=True)
        try:
            parser.parse_args()
        except HTTPException as e:
            raise InvalidHeaderException(e.code, e.data)

    @staticmethod
    def _create_bundle_response(entries):
        bundle = Bundle()
        bundle.type = 'searchset'
        bundle.entry = []
        bundle.total = len(entries)
        for item in entries:
            entry = BundleEntry()
            entry.fullUrl = '{}{}'.format(request.base_url, item.identifier[0].value.value)
            entry.resource = item
            bundle.entry.append(entry)
        return bundle

    def post(self, resource_type):
        resource = _get_resource('{}ListResource'.format(resource_type))

        self.validate_headers()

        item = resource.post()

        headers = dict(self.base_headers)
        headers.update({
            'Location': '{}/{}'.format(request.base_url, item.identifier[0].value.value),
        })
        return item.as_json(), 201, headers

    def get(self, resource_type):
        resource = _get_resource('{}ListResource'.format(resource_type))

        items = resource.get()

        bundle = self._create_bundle_response(items)
        return bundle.as_json(), 200, self.base_headers



