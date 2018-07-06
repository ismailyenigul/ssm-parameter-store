import os
import logging

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class EC2ParameterStore:
    def __init__(self):
        self.client = boto3.client('ssm')
        self.path_delimiter = '/'

    @classmethod
    def set_env(cls, parameter_dict):
        for k, v in parameter_dict.items():
            os.environ.setdefault(k, v)

    def _get_paginated_parameters(self, client_method, strip_path=True, **client_kwargs):
        next_token = None
        parameters = []
        while True:
            result = client_method(**client_kwargs)
            parameters += result.get('Parameters')
            next_token = result.get('NextToken')
            if next_token is None:
                break
            client_kwargs.update({'NextToken': next_token})
        return dict(self.extract_parameter(p, strip_path=strip_path) for p in parameters)

    def extract_parameter(self, parameter, strip_path=False):
        key = parameter['Name']
        if strip_path:
            key_parts = key.split(self.path_delimiter)
            key = key_parts[-1]
        value = parameter['Value']
        return (key, value)

    def get_parameter(self, name, decrypt=True, strip_path=True):
        result = self.client.get_parameter(Name=name, WithDecryption=decrypt)
        p = result['Parameter']
        return dict([self.extract_parameter(p, strip_path=strip_path)])

    def get_parameters(self, names, decrypt=True, strip_path=True):
        client_kwargs = dict(Names=names, WithDecryption=decrypt)
        return self._get_paginated_parameters(
            client_method=self.client.get_parameters,
            strip_path=strip_path,
            **client_kwargs
        )

    def get_parameters_by_path(self, path, decrypt=True, recursive=True, strip_path=True):
        client_kwargs = dict(Path=path, WithDecryption=decrypt, Recursive=recursive)
        return self._get_paginated_parameters(
            client_method=self.client.get_parameters_by_path,
            strip_path=strip_path,
            **client_kwargs
        )