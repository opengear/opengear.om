#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_system class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.cfg.base import (
    ConfigBase,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    to_list,
    dict_diff,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.facts.facts import Facts

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    get_restapi_body_structure,
    command_builder
)

from ansible.module_utils.connection import ConnectionError


class System(ConfigBase):
    """
    The om_system class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'system',
    ]

    def __init__(self, module):
        super(System, self).__init__(module)

    def get_system_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        system_facts = facts['ansible_network_resources'].get('system')
        if not system_facts:
            return {}
        return system_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_system_facts = self.get_system_facts()
        else:
            existing_system_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_system_facts))
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    try:
                        self._connection.send_request(command['data'], command['path'], command['method'])
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
            result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_system_facts = self.get_system_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_system_facts
            if result['changed']:
                result['after'] = changed_system_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_system_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_system_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_system_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """

        commands = []
        commands.extend(System._state_deleted(want, have))
        commands.extend(System._state_merged(want, have))
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        commands.extend(System._state_deleted(have, have))
        commands.extend(System._state_merged(want, have))
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        body_structure = get_restapi_body_structure()['system']
        commands = []
        to_set = dict_diff(have, want)
        for option in to_set.keys():
            if isinstance(to_set[option], list):
                for key in want[option]:
                    data = key
                    if 'id' in data:
                        data.pop('id')
                    data = {"system_authorized_key": data}
                    # command = {'data': data, 'path': 'system/' + option, 'method': 'POST'}
                    command = command_builder(data, 'system/' + option)
                    commands.append(command)
            elif option == 'reboot':
                command = {'data': None, 'path': 'system/reboot', 'method': 'POST'}
                commands.append(command)
            else:
                data = to_set[option]
                for key in reversed(body_structure[option]):
                    data = {key: data}
                # command = {'data': data, 'path': 'system/' + option, 'method': 'PUT'}
                command = command_builder(data, 'system/', option)
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """

        commands = []
        for option in want:
            if isinstance(want[option], list) and isinstance(have[option], list):
                device_ids = []
                for key in have[option]:
                    if 'id' in key:
                        device_ids.append(key['id'])
                for key in want[option]:
                    if 'id' in key and key['id'] in device_ids:
                        command = {'data': None, 'path': 'system/' + option + '/' + key['id'], 'method': 'DELETE'}
                        commands.append(command)
        return commands
