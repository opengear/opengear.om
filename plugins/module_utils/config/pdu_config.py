# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy
import json

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts
from ansible_collections.opengear.ng.plugins.module_utils.utils.utils import (
    command_builder,
    dict_diff,
    dict_merge,
    find_instance_id,
    remove_empties,
    to_list,
)

# Identification-only field that must not appear in PUT/POST request bodies
_TOP_BODY_EXCLUDE = frozenset({"id"})

# Nested settings blocks that carry a device-assigned "id" in facts (from
# serialPduSettingsID / snmpPduSettingsID) that the RAML's write bodies
# (serialPduSettings / snmpPduSettings) do not accept.
_NESTED_SETTINGS_KEYS = ("powerman", "shell", "snmp")


def _clean_pdu_body(data):
    """Strip identification-only fields the device rejects from a PDU dict
    before it is sent as a PUT/POST body: the top-level id, and the
    device-assigned id and read-only name nested under driver/powerman/
    shell/snmp (present in facts, but not part of the write schema)."""
    body = {k: v for k, v in data.items() if k not in _TOP_BODY_EXCLUDE}

    driver = body.get("driver")
    if isinstance(driver, dict):
        body["driver"] = {k: v for k, v in driver.items() if k != "name"}

    for key in _NESTED_SETTINGS_KEYS:
        settings = body.get(key)
        if isinstance(settings, dict):
            body[key] = {k: v for k, v in settings.items() if k != "id"}

    return body


def _outlets_equal(a, b):
    """Compare two outlet lists order-insensitively. dict_diff/sorted()
    cannot compare lists of dicts directly, so this is done separately."""
    def key(outlet):
        return json.dumps(outlet, sort_keys=True)
    return sorted(a or [], key=key) == sorted(b or [], key=key)


class PduConfig(ConfigBase):
    """
    Manages configuration for PDUs connected to Opengear devices.
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'pdu_config',
    ]

    def __init__(self, module):
        super(PduConfig, self).__init__(module)
        self.current_state = {}

    def get_pdu_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A list
        :returns: The current configuration as a list of PDU dicts
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data
        )
        pdu_facts = facts['ansible_network_resources'].get('pdu_config')
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
                        response = self._connection.send_request(
                            command['data'], command['path'], command['method']
                        )
                        if command['method'] in ('PUT', 'POST'):
                            updated_pdu = response.get('pdu', {})
                            pdu_id = updated_pdu.get('id') or command['path'].split('/')[-1]
                            if pdu_id:
                                self.current_state[pdu_id] = updated_pdu
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
            else:
                # Simulate state changes for check mode + diff
                for command in commands:
                    if command['method'] == 'PUT':
                        pdu_id = command['path'].split('/')[-1]
                        if pdu_id in self.current_state:
                            self.current_state[pdu_id].update(command['data']['pdu'])
            result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_pdu_facts = self.get_pdu_facts(self.current_state.values())
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_pdu_facts
            if result['changed']:
                result['after'] = changed_pdu_facts
                if self._module._diff:
                    diff_before = []
                    diff_after = []
                    existing_by_id = {
                        p['id']: p for p in existing_pdu_facts if p.get('id')
                    }
                    for command in commands:
                        if command['method'] == 'PUT':
                            pdu_id = command['path'].split('/')[-1]
                            if pdu_id in existing_by_id:
                                before = existing_by_id[pdu_id]
                                after = {**before, **command['data']['pdu']}
                                diff_before.append(before)
                                diff_after.append(after)
                    result['diff'] = {
                        'before': json.dumps(diff_before, indent=4) + '\n',
                        'after': json.dumps(diff_after, indent=4) + '\n',
                    }
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

        self.current_state = deepcopy(id_pdu_map)

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

        Delegates to merged: the device requires a complete PDU object on
        every PUT, so a partial replaced body is rejected outright.

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        return PduConfig._state_merged(want, name_id_map, id_pdu_map)

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
        commands.extend(PduConfig._state_deleted(deleted_pdus.values(), name_id_map))

        commands.extend(PduConfig._state_replaced(want, name_id_map, id_pdu_map))
        return commands

    @staticmethod
    def _state_merged(want, name_id_map, id_pdu_map):
        """ The command generator when state is merged

        Outlets are replaced wholesale rather than merged: they are keyed
        by outlet number, not by dict identity, so a generic dict_merge
        would append a new duplicate entry instead of updating the
        matching outlet.

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for pdu in want:
            data = remove_empties(pdu)
            pdu_id = find_instance_id(name_id_map, 'name', data)
            if pdu_id in id_pdu_map:
                device_pdu = deepcopy(id_pdu_map[pdu_id])
                outlets = data.pop('outlets', None)
                device_outlets = device_pdu.pop('outlets', None)
                merged_data = dict_merge(device_pdu, data)
                merged_outlets = outlets if outlets is not None else device_outlets
                changed = bool(dict_diff(merged_data, device_pdu)) or not _outlets_equal(
                    merged_outlets, device_outlets
                )
                if not changed:
                    continue
                merged_data['outlets'] = merged_outlets
                data = merged_data
                data.pop('id', None)
            else:
                pdu_id = None
            body = _clean_pdu_body(data)
            command = command_builder({'pdu': body}, 'pdus/', pdu_id)
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
