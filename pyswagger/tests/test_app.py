from pyswagger import SwaggerApp
from .utils import get_test_data_folder
from pyswagger.obj import (
    Info,
    Authorization,
    Scope,
    GrantType,
    Implicit,
    AuthorizationCode,
    LoginEndpoint,
    TokenRequestEndpoint,
    TokenEndpoint,
    Resource
)
import unittest


app = SwaggerApp._create_(get_test_data_folder(version='1.2', which='wordnik'))


class PropertyTestCase(unittest.TestCase):
    """ make sure properties' existence & type """

    def test_resource_list(self):
        """ resource list """
        self.assertIsInstance(app.info, Info)
        self.assertEqual(app.info.title, 'Swagger Sample App')
        self.assertEqual(app.swaggerVersion, '1.2')
        # description is ignored 
        with self.assertRaises(AttributeError):
            app.info.description

    def test_authorizations(self):
        """ authorizations """
        self.assertIn('oauth2', app.authorizations)
        self.assertIsInstance(app.authorizations['oauth2'], Authorization)
        self.assertEqual(app.authorizations['oauth2'].type, 'oauth2')

    def test_scope(self):
        """ scope """
        auth = app.authorizations['oauth2']
        self.assertEqual(len(auth.scopes), 2)
        self.assertIsInstance(auth.scopes[0], Scope)
        self.assertIsInstance(auth.scopes[0], Scope)
        self.assertEqual(auth.scopes[0].scope, 'write:pets')
        self.assertEqual(auth.scopes[1].scope, 'read:pets')
        with self.assertRaises(AttributeError):
            auth.scopes[1].description

    def test_grant_type(self):
        """ grant type """
        auth = app.authorizations['oauth2']
        self.assertIsInstance(auth.grantTypes, GrantType)

    def test_implicit(self):
        """ implicit """
        grant = app.authorizations['oauth2'].grantTypes
        self.assertIsInstance(grant.implicit, Implicit)
        self.assertEqual(grant.implicit.tokenName, 'access_token')

    def test_login_endpoint(self):
        """ login endpoint """
        implicit = app.authorizations['oauth2'].grantTypes.implicit
        self.assertIsInstance(implicit.loginEndpoint, LoginEndpoint)
        self.assertEqual(implicit.loginEndpoint.url,
            'http://petstore.swagger.wordnik.com/oauth/dialog')

    def test_authorization_code(self):
        """ authorization code """
        grant = app.authorizations['oauth2'].grantTypes
        self.assertIsInstance(grant.authorization_code, AuthorizationCode)

    def test_token_request_endpoint(self):
        """ token request endpoint """
        auth = app.authorizations['oauth2'].grantTypes.authorization_code
        self.assertIsInstance(auth.tokenRequestEndpoint,TokenRequestEndpoint)
        self.assertEqual(auth.tokenRequestEndpoint.url,
            'http://petstore.swagger.wordnik.com/oauth/requestToken')
        self.assertEqual(auth.tokenRequestEndpoint.clientIdName, 'client_id')
        self.assertEqual(auth.tokenRequestEndpoint.clientSecretName, 'client_secret')

    def test_token_endpoint(self):
        """ token endpoint """
        auth = app.authorizations['oauth2'].grantTypes.authorization_code
        self.assertIsInstance(auth.tokenEndpoint, TokenEndpoint)
        self.assertEqual(auth.tokenEndpoint.url,
            'http://petstore.swagger.wordnik.com/oauth/token')
        self.assertEqual(auth.tokenEndpoint.tokenName, 'auth_code')

    def test_resource_pet(self):
        """ resource """
        pet = app.apis['pet']
        self.assertIsInstance(pet, Resource)
        self.assertEqual(pet.swaggerVersion, '1.2')
        self.assertEqual(pet.apiVersion, '1.0.0')
        self.assertEqual(pet.basePath, 'http://petstore.swagger.wordnik.com/api')
        self.assertEqual(pet.resourcePath, '/pet')
        self.assertIn('application/json', pet.produces)
        self.assertIn('application/xml', pet.produces)
        self.assertIn('text/plain', pet.produces)
        self.assertIn('text/html', pet.produces)

    def test_operation(self):
        """ operation """
        pass

