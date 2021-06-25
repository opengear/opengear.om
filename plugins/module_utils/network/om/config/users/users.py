#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_users class
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
    dict_merge,
    remove_empties,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.facts.facts import Facts

from ansible.module_utils.connection import ConnectionError

from copy import deepcopy

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    command_builder,
    find_instance_id,
    is_subset,
)


class Users(ConfigBase):
    """
    The om_users class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'users',
    ]

    def __init__(self, module):
        super(Users, self).__init__(module)

    def get_users_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        users_facts = facts['ansible_network_resources'].get('users')
        if not users_facts:
            return []
        return users_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            existing_users_facts = self.get_users_facts()
            if self.state != 'gathered':
                commands.extend(self.set_config(existing_users_facts))
        else:
            existing_users_facts = {}
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    try:
                        self._connection.send_request(command['data'], command['path'], command['method'])
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
            result['changed'] = True
        result['commands'] = commands
        if self.state in self.ACTION_STATES:
            changed_users_facts = self.get_users_facts()
            result['before'] = existing_users_facts
            if result['changed']:
                result['after'] = changed_users_facts
        elif self.state == 'rendered':
            result['rendered'] = self._module.params['config']
        elif self.state == 'gathered':
            result['gathered'] = existing_users_facts
        result['warnings'] = warnings
        return result

    def set_config(self, existing_users_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_users_facts
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
        username_id_map = {}
        id_user_map = {}
        for user in have:
            username_id_map[user['username']] = user['id']
            id_user_map[user['id']] = user

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, username_id_map, id_user_map)
        elif state == 'deleted':
            commands = self._state_deleted(want, username_id_map)
        elif state == 'merged':
            commands = self._state_merged(want, username_id_map, id_user_map)
        elif state == 'replaced':
            commands = self._state_replaced(want, username_id_map, id_user_map)
        return commands

    @staticmethod
    def _state_replaced(want, username_id_map, id_user_map):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for user in want:
            user_id = find_instance_id(username_id_map, 'username', user)
            user = remove_empties(user)
            if user_id in id_user_map:
                data = deepcopy(user)
                data['id'] = user_id
                if is_subset(data, remove_empties(id_user_map[user_id])):
                    continue
                if 'groups' not in user or user['groups'] is None:
                    user['groups'] = []
            command = command_builder({'user': user}, 'users/', user_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, username_id_map, id_user_map):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        deleted_users = deepcopy(id_user_map)

        for user in want:
            if 'id' in user and user['id'] in id_user_map:
                user_id = user['id']
            else:
                user_id = find_instance_id(username_id_map, 'username', user)
            if user_id in deleted_users:
                deleted_users.pop(user_id)
        commands.extend(Users._state_deleted(deleted_users.values(), username_id_map))

        commands.extend(Users._state_replaced(want, username_id_map, id_user_map))
        return commands

    @staticmethod
    def _state_merged(want, username_id_map, id_user_map):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for user in want:
            data = remove_empties(user)
            user_id = find_instance_id(username_id_map, 'username', data)
            if user_id in id_user_map:
                device_user = id_user_map[user_id]
                if 'password' in data:
                    device_user.pop('hashed_password')
                elif 'hashed_password' in data:
                    device_user.pop('password')
                merged_data = dict_merge(device_user, data)
                if is_subset(merged_data, device_user):
                    continue
                else:
                    data = merged_data
                data.pop('id', None)
            else:
                user_id = None
            command = command_builder({'user': data}, 'users/', user_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, username_id_map):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for user in want:
            user_id = find_instance_id(username_id_map, 'username', user)
            command = command_builder(None, 'users/', user_id, ['users-1'])
            if command:
                commands.append(command)
        return commands
