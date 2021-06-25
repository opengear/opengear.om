#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_groups class
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

from ansible.module_utils.connection import ConnectionError

from copy import deepcopy

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    command_builder,
    find_instance_id,
)


class Groups(ConfigBase):
    """
    The om_groups class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'groups',
    ]

    def __init__(self, module):
        super(Groups, self).__init__(module)
        self.current_state = None

    def get_groups_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data)
        groups_facts = facts['ansible_network_resources'].get('groups')
        if not groups_facts:
            return []
        return groups_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_groups_facts = self.get_groups_facts()
        else:
            existing_groups_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_groups_facts))
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    group_id = None
                    if command['method'] in ['PUT', 'DELETE']:
                        group_id = command['path'].split('/')[-1]
                    try:
                        response = self._connection.send_request(command['data'], command['path'], command['method'])
                        if group_id and command['method'] == 'PUT':
                            self.current_state[group_id] = response['group']
                        else:
                            self.current_state[response['group']['id']] = response['group']
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
                        self.current_state.pop(group_id, None)
            result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_groups_facts = self.get_groups_facts(self.current_state.values())
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_groups_facts
            if result['changed']:
                result['after'] = changed_groups_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_groups_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_groups_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_groups_facts
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
        groupname_id_map = {}
        id_group_map = {}
        for group in have:
            groupname_id_map[group['groupname']] = group['id']
            id_group_map[group['id']] = group

        self.current_state = deepcopy(id_group_map)

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, groupname_id_map, id_group_map)
        elif state == 'deleted':
            commands = self._state_deleted(want, groupname_id_map)
        elif state == 'merged':
            commands = self._state_merged(want, groupname_id_map, id_group_map)
        elif state == 'replaced':
            commands = self._state_replaced(want, groupname_id_map, id_group_map)
        return commands

    @staticmethod
    def _state_replaced(want, groupname_id_map, id_group_map):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for group in want:
            group_id = find_instance_id(groupname_id_map, 'groupname', group)
            if group_id in id_group_map:
                data = remove_empties(group)
                data['id'] = group_id
                if data == remove_empties(id_group_map[group_id]):
                    continue
            command = command_builder({'group': group}, 'groups/', group_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, groupname_id_map, id_group_map):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        deleted_groups = deepcopy(id_group_map)

        for group in want:
            if 'id' in group and group['id'] in id_group_map:
                group_id = group['id']
            else:
                group_id = find_instance_id(groupname_id_map, 'groupname', group)
            if group_id in deleted_groups:
                deleted_groups.pop(group_id)
        commands.extend(Groups._state_deleted(deleted_groups.values(), groupname_id_map))

        commands.extend(Groups._state_replaced(want, groupname_id_map, id_group_map))
        return commands

    @staticmethod
    def _state_merged(want, groupname_id_map, id_group_map):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for group in want:
            data = remove_empties(group)
            group_id = find_instance_id(groupname_id_map, 'groupname', data)
            if group_id in id_group_map:
                device_group = id_group_map[group_id]
                merged_data = dict_merge(device_group, data)
                if dict_diff(merged_data, device_group):
                    data = merged_data
                else:
                    continue
                data.pop('id', None)
            else:
                group_id = None
            command = command_builder({'group': data}, 'groups/', group_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, groupname_id_map):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for group in want:
            group_id = find_instance_id(groupname_id_map, 'groupname', group)
            command = command_builder(None, 'groups/', group_id, ['groups-1'])
            if command:
                commands.append(command)
        return commands
