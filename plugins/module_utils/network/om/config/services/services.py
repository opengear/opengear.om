#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_services class
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
    dict_merge,
    remove_empties,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.facts.facts import Facts

from copy import deepcopy

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    command_builder,
    find_instance_id,
)


def get_name_id_map(instance_list):
    name_id_map = {}
    for instance in instance_list:
        name_id_map[instance['name']] = instance['id']
    return name_id_map


def get_id_instance_map(instance_list):
    id_instance_map = {}
    for instance in instance_list:
        id_instance_map[instance['id']] = instance
    return id_instance_map


class Services(ConfigBase):
    """
    The om_services class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'services',
    ]

    def __init__(self, module):
        super(Services, self).__init__(module)

    def get_services_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        services_facts = facts['ansible_network_resources'].get('services')
        if not services_facts:
            return []
        return services_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_services_facts = self.get_services_facts()
        else:
            existing_services_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_services_facts))
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
            changed_services_facts = self.get_services_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_services_facts
            if result['changed']:
                result['after'] = changed_services_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_services_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_services_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_services_facts
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
        want = remove_empties(want)
        for option in want:
            if isinstance(want[option], list):
                name_id_map = get_name_id_map(have[option])
                id_instance_map = get_id_instance_map(have[option])
                for instance in want[option]:
                    instance_id = find_instance_id(name_id_map, 'name', instance)
                    if instance_id in id_instance_map:
                        data = remove_empties(instance)
                        data['id'] = instance_id
                        if data == remove_empties(id_instance_map[instance_id]):
                            continue
                    if option == 'syslog':
                        key = 'syslogServer'
                    else:
                        key = 'snmp_alert_manager'
                    command = command_builder({key: data}, 'services/' + option + '/', instance_id)
                    if command:
                        commands.append(command)
            else:
                command = command_builder({option: want[option]}, 'services/', option)
                if command:
                    commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for option in want:
            if isinstance(want[option], list):
                name_id_map = get_name_id_map(have[option])
                id_instance_map = get_id_instance_map(have[option])
                deleted_instances = deepcopy(id_instance_map)
                for instance in want[option]:
                    if 'id' in instance and instance['id'] in id_instance_map:
                        instance_id = instance['id']
                    else:
                        instance_id = find_instance_id(name_id_map, 'name', instance)
                    if instance_id in deleted_instances:
                        deleted_instances.pop(instance_id)
                commands.extend(Services._delete_instance(deleted_instances.values(), name_id_map, option + '/'))

        commands.extend(Services._state_replaced(want, have))
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for option in want:
            path = 'services/'
            if isinstance(want[option], list):
                name_id_map = get_name_id_map(have[option])
                id_instance_map = get_id_instance_map(have[option])
                for instance in want[option]:
                    instance_id = find_instance_id(name_id_map, 'name', instance)
                    if instance_id in id_instance_map:
                        device_instance = id_instance_map[instance_id]
                        data = remove_empties(instance)
                        data['id'] = instance_id
                        merged_data = dict_merge(device_instance, data)
                        if dict_diff(merged_data, device_instance):
                            data = merged_data
                        else:
                            continue
                    if option == 'syslog':
                        key = 'syslogServer'
                    else:
                        key = 'snmp_alert_manager'
                    command = command_builder({key: data}, path + option + '/', instance_id)
                    if command:
                        commands.append(command)
            else:
                command = command_builder({option: want[option]}, path, option)
                if command:
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
            if isinstance(want[option], list):
                name_id_map = get_name_id_map(have[option])
                commands.extend(Services._delete_instance(want, name_id_map, option + '/'))
        return commands

    @staticmethod
    def _delete_instance(want, name_id_map, path):
        commands = []
        for instance in want:
            instance_id = find_instance_id(name_id_map, 'name', instance)
            command = command_builder(None, path, instance_id)
            if command:
                commands.append(command)
        return commands
