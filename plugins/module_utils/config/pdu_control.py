# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase


def _find_pdu_id(name_id_map, entry):
    """Resolve PDU identity from id or name. Pops consumed keys."""
    pdu_id = entry.pop('id', None)
    if pdu_id:
        return pdu_id
    name = entry.get('name')
    if name and name in name_id_map:
        return name_id_map[name]
    return None


def _build_name_id_map(connection):
    """Fetch the PDU list and return a name -> id map."""
    try:
        data = connection.send_request(None, 'pdus')
        name_id_map = {}
        for pdu in data.get('pdus', []):
            pid = pdu.get('id')
            pname = pdu.get('name')
            if pid and pname:
                name_id_map[pname] = pid
        return name_id_map
    except Exception:
        return {}


def _build_command(pdu_id, outlets, action):
    """Build the API command to send an action to a PDU's outlets."""
    return {
        'data': {
            'pdu_outlets': {
                'outlets': [{'number': number} for number in outlets],
                'action': action,
            },
        },
        'path': 'pdus/' + pdu_id + '/outlets',
        'method': 'PUT',
    }


class PduControl(ConfigBase):
    """
    Sends power actions (on, off, cycle) to PDU outlets on Opengear devices.

    This is an action module, it is always considered changed when commands
    are issued. Use check mode to preview commands without sending them.
    """

    def __init__(self, module):
        super(PduControl, self).__init__(module)

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = []

        name_id_map = _build_name_id_map(self._connection)

        for entry in self._module.params['config']:
            entry = deepcopy(entry)
            pdu_id = _find_pdu_id(name_id_map, entry)
            outlets = entry.get('outlets')
            action = entry.get('action')
            if not pdu_id or not outlets or not action:
                continue
            commands.append(_build_command(pdu_id, outlets, action))

        if commands:
            if not self._module.check_mode:
                for command in commands:
                    try:
                        self._connection.send_request(
                            command['data'], command['path'], command['method']
                        )
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
            result['changed'] = True

        result['commands'] = commands
        return result
