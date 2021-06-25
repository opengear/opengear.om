#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om system fact class
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
from ansible_collections.opengear.om.plugins.module_utils.network.om.argspec.system.system import SystemArgs

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    get_restapi_body_structure,
)


class SystemFacts(object):
    """ The om system fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = SystemArgs.argument_spec
        self.body_structure = get_restapi_body_structure()['system']
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
            if option == 'reboot':
                value = {'reboot': False}
            elif option == 'cell_reliability_test':
                value = {'cell_reliability_test': None}
            else:
                value = {option: connection.get(None, 'system/' + option)}
            data.update(value)
        return data

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for system
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = self.get_device_data(connection)
        obj = {}
        if data:
            obj.update(self.render_config(self.generated_spec, data))

        ansible_facts['ansible_network_resources'].pop('system', None)
        facts = {}
        if obj:
            params = utils.validate_config(self.argument_spec, {'config': obj})
            facts['system'] = params['config']
        else:
            facts['system'] = {}

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
        for option in conf.keys():
            value = conf[option]
            if isinstance(conf[option], dict):
                option_structure = self.body_structure[option]
                for key in option_structure:
                    value = value[key]
            config[option] = value
        for key in config['system_authorized_keys']:
            if 'key_fingerprint' in key:
                key.pop('key_fingerprint')
        return utils.remove_empties(config)
