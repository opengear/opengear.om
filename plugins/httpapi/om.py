from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase

def handle_response(response):
    if response:
        handled_response = json.loads(response.getvalue())
        if "error" in handled_response:
            error = handled_response["error"][0]
            raise ConnectionError(error["text"], code=error["code"])
        return handled_response
    return response


class HttpApi(HttpApiBase):

    def __init__(self, *args, **kwargs):
        super(HttpApi, self).__init__(*args, **kwargs)
        self._device_info = None
        self.path = '/api/v2/'

    def login(self, username, password):
        login_path = 'sessions/'
        data = {'username': username, 'password': password}
        response = self.send_request(data, login_path, 'POST')
        self.connection._auth = {'Authorization': 'Token ' + response['session']}

    def get(self, command, path):
        return self.send_request(data=command, path=path)

    def send_request(self, data, path, method='GET'):
        headers = {'Content-Type': 'application/json'}
        response, response_content = self.connection.send(self.path + path, json.dumps(data),
                                                          method=method, headers=headers)
        return handle_response(response_content)

    def logout(self):
        logout_path = 'sessions/self'
        self.send_request(None, logout_path, method='DELETE')
        self.connection._auth = None

    def get_device_info(self):
        if self._device_info:
            return self._device_info

        device_info = {}
        version_reply = self.send_request(None, 'system/version')['system_version']

        device_info['firmware_version'] = version_reply['firmware_version']
        device_info['rest_api_version'] = version_reply['rest_api_version']

        endpoints = ['hostname', 'serial_number', 'model_name']
        for endpoint in endpoints:
            device_info[endpoint] = self.send_request(None, 'system/' + endpoint)['system_' + endpoint][endpoint]
        self._device_info = device_info
        return self._device_info

    def get_capabilities(self):
        result = {'device_info': self.get_device_info()}
        return json.dumps(result)
