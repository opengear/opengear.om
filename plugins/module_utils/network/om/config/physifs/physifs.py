#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_physifs class
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
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    to_list,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.facts.facts import Facts

from ansible.module_utils.connection import ConnectionError

from copy import deepcopy


class Physifs(ConfigBase):
    """
    The om_physifs class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'physifs',
    ]

    def __init__(self, module):
        super(Physifs, self).__init__(module)

    def get_physifs_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        physifs_facts = facts['ansible_network_resources'].get('physifs')
        if not physifs_facts:
            return []
        return physifs_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_physifs_facts = self.get_physifs_facts()
        else:
            existing_physifs_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_physifs_facts))
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
            changed_physifs_facts = self.get_physifs_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_physifs_facts
            if result['changed']:
                result['after'] = changed_physifs_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_physifs_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_physifs_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_physifs_facts
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
        physifname_id_map = {}
        id_physif_map = {}
        for physif in have:
            physifname_id_map[physif['name']] = physif['id']
            id_physif_map[physif['id']] = physif

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, physifname_id_map, id_physif_map)
        elif state == 'deleted':
            commands = self._state_deleted(want, physifname_id_map)
        elif state == 'merged':
            commands = self._state_merged(want, physifname_id_map, id_physif_map)
        elif state == 'replaced':
            commands = self._state_replaced(want, physifname_id_map, id_physif_map)
        return commands

    @staticmethod
    def _state_replaced(want, physifname_id_map, id_physif_map):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for physif in want:
            physif_id = physif.pop('id', None)
            if not physif_id and 'name' in physif and physif['name'] in physifname_id_map:
                physif_id = physifname_id_map[physif['name']]
            if physif_id in id_physif_map:
                data = remove_empties(physif)
                data['id'] = physif_id
                if data == remove_empties(id_physif_map[physif_id]):
                    continue
                if 'slaves' not in physif or physif['slaves'] is None:
                    physif['slaves'] = []
            if physif_id:
                command = {'data': {'physif': physif}, 'path': 'physifs/' + physif_id, 'method': 'PUT'}
            else:
                command = {'data': {'physif': physif}, 'path': 'physifs', 'method': 'POST'}
            commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, physifname_id_map, id_physif_map):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        deleted_physifs = deepcopy(id_physif_map)

        for physif in want:
            physif_id = None
            if 'id' in physif and physif['id'] in id_physif_map:
                physif_id = physif['id']
            elif 'name' in physif and physif['name'] in physifname_id_map:
                physif_id = physifname_id_map[physif['name']]
            if physif_id in deleted_physifs:
                deleted_physifs.pop(physif_id)
        commands.extend(Physifs._state_deleted(deleted_physifs.values(), physifname_id_map))

        commands.extend(Physifs._state_replaced(want, physifname_id_map, id_physif_map))
        return commands

    @staticmethod
    def _state_merged(want, physifname_id_map, id_physif_map):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for physif in want:
            data = remove_empties(physif)
            physif_id = data.pop('id', None)
            if not physif_id and 'name' in data and data['name'] in physifname_id_map:
                physif_id = physifname_id_map[data['name']]
            if physif_id in id_physif_map:
                device_physif = id_physif_map[physif_id]
                if 'password' in data:
                    device_physif.pop('hashed_password')
                elif 'hashed_password' in data:
                    device_physif.pop('password')
                merged_data = dict_merge(device_physif, data)
                if dict_diff(merged_data, device_physif):
                    data = merged_data
                else:
                    data = {}
                data.pop('id', None)
            else:
                physif_id = None
            if data:
                if physif_id:
                    command = {'data': {'physif': data}, 'path': 'physifs/' + physif_id, 'method': 'PUT'}
                else:
                    command = {'data': {'physif': data}, 'path': 'physifs', 'method': 'POST'}
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, physifname_id_map):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for physif in want:
            physif_id = physif.pop('id', None)
            if not physif_id and 'name' in physif and physif['name'] in physifname_id_map:
                physif_id = physifname_id_map[physif['name']]
            if physif_id:
                command = {'data': None, 'path': 'physifs/' + physif_id, 'method': 'DELETE'}
                commands.append(command)
        return commands
