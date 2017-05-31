#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016, Florent Thiery
# https://github.com/holacracyone/glassfrog-api/tree/API_v3

import os
import sys
import time
import math
import hashlib
import requests
import json

session = None

# Do not edit this directly, create a config.json file instead
CONFIG_DEFAULT = {
    'SERVER_URL': 'https://api.glassfrog.com/api/v3/',
    'API_KEY': 'my-api-client',
    'PROXIES': {'http': '', 'https': ''},
    'VERIFY_SSL': True,
}


def save_config(config_dict, config_fpath):
    with open(config_fpath, 'w') as config_file:
        json.dump(config_dict, config_file, sort_keys=True, indent=4, separators=(',', ': '))


def read_config(config_fpath):
    print('Reading %s' % config_fpath)
    with open(config_fpath, 'r') as config_file:
        return json.load(config_file)


class GlassfrogClient:

    def __init__(self, config=None, configFilename=None):
        #if filename is provided instead of config object, use that
        if config==None and not configFilename==None:
            config = GlassfrogClient.read_config(configFilename)
        self.config = config
        if not config['VERIFY_SSL']:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    @staticmethod
    def read_config(config_fpath):
        print('Reading %s' % config_fpath)
        with open(config_fpath, 'r') as config_file:
            return json.load(config_file)

    def request(self, url, method='get', data={}, params={}, files={}, headers={}, json=True, timeout=10):
        global session
        if session is None:
            session = requests.Session()

        headers['X-Auth-Token'] = self.config['API_KEY']
        if method == 'get':
            req_function = session.get
        else:
            req_function = session.post

        req_args = {
            'url': url,
            'headers': headers,
            'params': params,
            'data': data,
            'timeout': timeout,
            'proxies': self.config['PROXIES'],
            'verify': self.config['VERIFY_SSL'],
            'files': files,
        }
        resp = req_function(**req_args)
        if resp.status_code != 200:
            raise Exception('HTTP %s error on %s: %s' % (resp.status_code, url, resp.text))
        return resp.json() if json else resp.text.strip()

    def api(self, suffix, *args, **kwargs):
        BASE_URL = self.config['SERVER_URL']
        kwargs['url'] = requests.compat.urljoin(BASE_URL, suffix)
        return self.request(*args, **kwargs)

    def get_circles(self, circle_id=None, include_members=False):
        apiargs = {}
        if include_members:
            apiargs['include'] = 'members'
        if circle_id is None:
            return self.api('circles', params=apiargs)
        else:
            return self.api('circles/%s' % circle_id, params=apiargs)

    def get_people(self, person_id=None, circle_id=None, role_name=None):
        apiargs = {}
        if circle_id:
            apiargs['circle_id'] = circle_id
        if role_name:
            apiargs['role'] = role_name

        if person_id is None:
            return self.api('people', params=apiargs)
        else:
            return self.api('people/%s' % person_id, params=apiargs)

    def get_roles(self, role_id=None, person_id=None, circle_id=None):
        apiargs = {}
        if person_id:
            apiargs['person_id'] = person_id
        if circle_id:
            apiargs['circle_id'] = circle_id

        if role_id is None:
            return self.api('roles', params=apiargs)
        else:
            return self.api('roles/%s' % role_id, params=apiargs)

    def get_projects(self, circle_id):
        apiargs = {}
        return self.api('circles/%s/metrics' % circle_id, params=apiargs)

    def get_metric(self, circle_id=None, metric_id=None, include_global=True):
        apiargs = {}
        if not include_global:
            apiargs['global'] = False
        if circle_id is None:
            return self.api('metrics', params=apiargs)
        else:
            return self.api('circles/%s/metrics' % circle_id, params=apiargs)


if __name__ == '__main__':
    try:
        config_fpath = sys.argv[1]
    except IndexError:
        config_fpath = 'config.json'
    try:
        config = read_config(config_fpath)
        for k in CONFIG_DEFAULT.keys():
            changed = False
            if config.get(k) is None:
                config[k] = CONFIG_DEFAULT[k]
                changed = True
        if changed:
            save_config(config, config_fpath)
            print('Config updated and saved to %s' % config_fpath)
    except Exception as e:
        print('Error while parsing configuration file, using defaults (%s)' % e)
        config = CONFIG_DEFAULT

    gf = GlassfrogClient(config)
    #print(gf.get_circle())