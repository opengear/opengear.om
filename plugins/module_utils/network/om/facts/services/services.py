#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om services fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.argspec.services.services import ServicesArgs


class ServicesFacts(object):
    """ The om services fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = ServicesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection):
        data = {}
        for option in self.generated_spec.keys():
            value = connection.get(None, 'services/' + option)
            if option == 'syslog':
                value = {option: value['syslogServers']}
            data.update(value)
        return data

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for services
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = self.get_device_data(connection)

        obj = {}
        if data:
            obj.update(self.render_config(self.generated_spec, data))

        ansible_facts['ansible_network_resources'].pop('services', None)
        facts = {}
        if obj:
            params = utils.validate_config(self.argument_spec, {'config': obj})
            facts['services'] = params['config']
        else:
            facts['services'] = {}

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        for option in config.keys():
            if option in conf:
                if isinstance(conf[option], dict):
                    config[option] = self.render_config(config[option], conf[option])
                else:
                    config[option] = conf[option]
        return utils.remove_empties(config)
