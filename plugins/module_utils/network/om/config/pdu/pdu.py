#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_pdu class
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


class Pdu(ConfigBase):
    """
    The om_pdu class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'pdu',
    ]

    def __init__(self, module):
        super(Pdu, self).__init__(module)

    def get_pdu_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        pdu_facts = facts['ansible_network_resources'].get('pdu')
        if not pdu_facts:
            return []
        return pdu_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_pdu_facts = self.get_pdu_facts()
        else:
            existing_pdu_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_pdu_facts))
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
            changed_pdu_facts = self.get_pdu_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_pdu_facts
            if result['changed']:
                result['after'] = changed_pdu_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_pdu_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_pdu_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_pdu_facts
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
        name_id_map = {}
        id_pdu_map = {}
        for pdu in have:
            name_id_map[pdu['name']] = pdu['id']
            id_pdu_map[pdu['id']] = pdu

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, name_id_map, id_pdu_map)
        elif state == 'deleted':
            commands = self._state_deleted(want, name_id_map)
        elif state == 'merged':
            commands = self._state_merged(want, name_id_map, id_pdu_map)
        elif state == 'replaced':
            commands = self._state_replaced(want, name_id_map, id_pdu_map)
        return commands

    @staticmethod
    def _state_replaced(want, name_id_map, id_pdu_map):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for pdu in want:
            pdu_id = find_instance_id(name_id_map, 'name', pdu)
            if pdu_id in id_pdu_map:
                data = remove_empties(pdu)
                data['id'] = pdu_id
                if data == remove_empties(id_pdu_map[pdu_id]):
                    continue
            command = command_builder({'pdu': pdu}, 'pdus/', pdu_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, name_id_map, id_pdu_map):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        deleted_pdus = deepcopy(id_pdu_map)

        for pdu in want:
            if 'id' in pdu and pdu['id'] in id_pdu_map:
                pdu_id = pdu['id']
            else:
                pdu_id = find_instance_id(name_id_map, 'name', pdu)
            if pdu_id in deleted_pdus:
                deleted_pdus.pop(pdu_id)
        commands.extend(Pdu._state_deleted(deleted_pdus.values(), name_id_map))

        commands.extend(Pdu._state_replaced(want, name_id_map, id_pdu_map))
        return commands

    @staticmethod
    def _state_merged(want, name_id_map, id_pdu_map):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for pdu in want:
            data = remove_empties(pdu)
            pdu_id = find_instance_id(name_id_map, 'name', data)
            if pdu_id in id_pdu_map:
                device_pdu = id_pdu_map[pdu_id]
                merged_data = dict_merge(device_pdu, data)
                if dict_diff(merged_data, device_pdu):
                    data = merged_data
                else:
                    continue
                data.pop('id', None)
            else:
                pdu_id = None
            command = command_builder({'pdu': data}, 'pdus/', pdu_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want, name_id_map):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for pdu in want:
            pdu_id = find_instance_id(name_id_map, 'name', pdu)
            command = command_builder(None, 'pdus/', pdu_id)
            if command:
                commands.append(command)
        return commands
