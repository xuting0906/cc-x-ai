import json
import urllib.parse
from dataclasses import dataclass

import requests
from flask_login import current_user

from extensions.ext_database import db
from models.source import DataSourceBinding


@dataclass
class OAuthUserInfo:
    id: str
    name: str
    email: str


class OAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self):
        raise NotImplementedError()

    def get_access_token(self, code: str):
        raise NotImplementedError()

    def get_raw_user_info(self, token: str):
        raise NotImplementedError()

    def get_user_info(self, token: str) -> OAuthUserInfo:
        raw_info = self.get_raw_user_info(token)
        return self._transform_user_info(raw_info)

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        raise NotImplementedError()


class CCTalkOAuth(OAuth):
    _AUTH_URL = 'http://192.168.15.130:11000/open/auth'
    _TOKEN_URL = 'http://192.168.15.130:11000/open/token'
    _USER_INFO_URL = 'http://192.168.15.130:11000/open/me'
    # _EMAIL_INFO_URL = 'https://api.github.com/user/emails'

    def get_authorization_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile',  # Request only basic user information
            'response_type': 'code',
            'state': '123456789',
        }
        print(f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}")
        return f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        print(data)
        headers = {'Accept': 'application/json'}
        response = requests.post(self._TOKEN_URL, data=data, headers=headers)

        response_json = response.json()
        access_token = response_json.get('access_token')

        if not access_token:
            raise ValueError(f"Error in CCtalk OAuth: {response_json}")

        return access_token

    def get_raw_user_info(self, token: str):
        headers = {'Authorization': f"Bearer {token}"}
        response = requests.get(self._USER_INFO_URL, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        
        print(user_info)

        # email_response = requests.get(self._EMAIL_INFO_URL, headers=headers)
        # email_info = email_response.json()
        # primary_email = next((email for email in email_info if email['primary'] == True), None)

        # return {**user_info, 'email': primary_email['email']}
        print(">>>>>>>>>>>>>>>>>>",user_info)
        return {**user_info}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        print("-----------------------------",raw_info)
        email = raw_info.get('email')
        if not email:
            email = f"{raw_info['sub']}+{raw_info['discriminator']}@users.noreply.e-u.cn"
        print(str(raw_info['sub']))
        print(email)
        print(raw_info['nickname'])
        print("-----------------------------")
        return OAuthUserInfo(
            id=str(raw_info['sub']),
            name=raw_info['nickname'],
            email=email
        )
        
class GitHubOAuth(OAuth):
    _AUTH_URL = 'https://github.com/login/oauth/authorize'
    _TOKEN_URL = 'https://github.com/login/oauth/access_token'
    _USER_INFO_URL = 'https://api.github.com/user'
    _EMAIL_INFO_URL = 'https://api.github.com/user/emails'

    def get_authorization_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'user:email'  # Request only basic user information
        }
        return f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {'Accept': 'application/json'}
        response = requests.post(self._TOKEN_URL, data=data, headers=headers)

        response_json = response.json()
        access_token = response_json.get('access_token')

        if not access_token:
            raise ValueError(f"Error in GitHub OAuth: {response_json}")

        return access_token

    def get_raw_user_info(self, token: str):
        headers = {'Authorization': f"token {token}"}
        response = requests.get(self._USER_INFO_URL, headers=headers)
        response.raise_for_status()
        user_info = response.json()

        email_response = requests.get(self._EMAIL_INFO_URL, headers=headers)
        email_info = email_response.json()
        primary_email = next((email for email in email_info if email['primary'] == True), None)

        return {**user_info, 'email': primary_email['email']}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        email = raw_info.get('email')
        if not email:
            email = f"{raw_info['id']}+{raw_info['login']}@users.noreply.github.com"
        return OAuthUserInfo(
            id=str(raw_info['id']),
            name=raw_info['name'],
            email=email
        )


class GoogleOAuth(OAuth):
    _AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    _TOKEN_URL = 'https://oauth2.googleapis.com/token'
    _USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    def get_authorization_url(self):
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid email'
        }
        return f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        headers = {'Accept': 'application/json'}
        response = requests.post(self._TOKEN_URL, data=data, headers=headers)

        response_json = response.json()
        access_token = response_json.get('access_token')

        if not access_token:
            raise ValueError(f"Error in Google OAuth: {response_json}")

        return access_token

    def get_raw_user_info(self, token: str):
        headers = {'Authorization': f"Bearer {token}"}
        response = requests.get(self._USER_INFO_URL, headers=headers)
        response.raise_for_status()
        return response.json()

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=str(raw_info['sub']),
            name=None,
            email=raw_info['email']
        )


