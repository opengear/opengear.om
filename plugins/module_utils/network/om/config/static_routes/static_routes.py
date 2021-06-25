#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_static routes class
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


class StaticRoutes(ConfigBase):
    """
    The om_static routes class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'static_routes',
    ]

    def __init__(self, module):
        super(StaticRoutes, self).__init__(module)

    def get_static_routes_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        static_routes_facts = facts['ansible_network_resources'].get('static_routes')
        if not static_routes_facts:
            return []
        return static_routes_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_static_routes_facts = self.get_static_routes_facts()
        else:
            existing_static_routes_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_static_routes_facts))
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
            changed_static_routes_facts = self.get_static_routes_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_static_routes_facts
            if result['changed']:
                result['after'] = changed_static_routes_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_static_routes_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_static_routes_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_static_routes_facts
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
        destination_id_map = {}
        id_route_map = {}
        for route in have:
            destination_id_map[route['destination_address']] = route['id']
            id_route_map[route['id']] = route

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, destination_id_map, id_route_map)
        elif state == 'deleted':
            commands = self._state_deleted(want, destination_id_map)
        elif state == 'merged':
            commands = self._state_merged(want, destination_id_map, id_route_map)
        elif state == 'replaced':
            commands = self._state_replaced(want, destination_id_map, id_route_map)
        return commands

    @staticmethod
    def _state_replaced(want, destination_id_map, id_route_map):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for route in want:
            route_id = find_instance_id(destination_id_map, 'destination_address', route)
            if route_id in id_route_map:
                data = remove_empties(route)
                data['id'] = route_id
                if data == remove_empties(id_route_map[route_id]):
                    continue
            command = command_builder({'static_route': route}, 'static_routes/', route_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, destination_id_map, id_route_map):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        deleted_routes = deepcopy(id_route_map)

        for route in want:
            if 'id' in route and route['id'] in id_route_map:
                route_id = route['id']
            else:
                route_id = find_instance_id(destination_id_map, 'destination_address', route)
            if route_id in deleted_routes:
                deleted_routes.pop(route_id)

        if len(deleted_routes) == len(id_route_map):
            commands.append({'data': {'static_routes': want}, 'path': 'static_routes/', 'method': 'PUT'})
        else:
            commands.extend(StaticRoutes._state_deleted(deleted_routes.values(), destination_id_map))
            commands.extend(StaticRoutes._state_replaced(want, destination_id_map, id_route_map))

        return commands

    @staticmethod
    def _state_merged(want, destination_id_map, id_route_map):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for route in want:
            data = remove_empties(route)
            route_id = find_instance_id(destination_id_map, 'destination_address', data)
            if route_id in id_route_map:
                device_route = id_route_map[route_id]
                merged_data = dict_merge(device_route, data)
                if dict_diff(merged_data, device_route):
                    data = merged_data
                else:
                    continue
                data.pop('id', None)
            else:
                route_id = None
            command = command_builder({'static_route': data}, 'static_routes/', route_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, destination_id_map):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for route in want:
            route_id = find_instance_id(destination_id_map, 'destination_address', route)
            command = command_builder(None, 'static_routes/', route_id)
            if command:
                commands.append(command)
        return commands
