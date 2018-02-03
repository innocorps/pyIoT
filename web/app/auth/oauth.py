"""OAuth functions that interface with the providers oauth API"""
import json
from urllib.request import urlopen
from rauth import OAuth2Service
from flask import current_app, url_for, request, redirect


class OAuthSignIn(object):
    """
    Gets the provider and authentication data from
    the params and the config file.

    Returns:
        The url for the callback after authentication.
        The provider (ie. Google, Facebook) from the url.
    """

    providers = None

    def __init__(self, provider_name):
        """
        Pulls the credentials from the config file based on provider_name
        """
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def get_callback_url(self):
        """
        Creates the callback url that the provider will use

        Returns:
            The callback url that the provider will go
            back to once authentication is complete.
        """
        return url_for('auth.oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        """
        Gets the provider and its information from the config file

        Args:
            provider_name: provider being used for the
            authentication (ie. Google)

        Returns:
            self.providers: the provider and its information from config

        """
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):
    """
    Function that handles the Google OAuth2 signin

    Args:
        OAuthSignIn: takes this class that handles getting the provider a
        and all of its information.
    """

    def __init__(self):
        """
        Gets the correct google information and uses the Rauth OAuth2Service to
        communicate with the google OAuth2 API
        """
        super(GoogleSignIn, self).__init__('google')
        googleinfo = urlopen(
            'https://accounts.google.com/.well-known/openid-configuration')
        # Gets correct google_parameters through openid json
        google_params = json.load(googleinfo)
        self.service = OAuth2Service(
            name='google',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url=google_params.get('authorization_endpoint'),
            base_url=google_params.get('userinfo_endpoint'),
            access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        """
        Goes to the providers authorization url.

        Returns:
            The redirect towards the authorzation url
            build with the code and callback url.
        """
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        """
        Catches the callback from the provider.

        Returns:
            data used to create user profile.
        """
        if 'code' not in request.args:
            return None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            decoder=json.loads
        )
        me = oauth_session.get('').json()
        return (me['name'],
                me['email'])
