# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase

_POWER_COMMANDS = frozenset({'on', 'off', 'cycle'})


def _find_port_id(portnum_id_map, name_id_map, port):
    """Resolve port identity from id, portnum, or name. Pops consumed keys."""
    port_id = port.pop('id', None)
    if port_id:
        return port_id
    portnum = port.pop('portnum', None)
    if portnum is not None and portnum in portnum_id_map:
        return portnum_id_map[portnum]
    name = port.get('name')
    if name and name in name_id_map:
        return name_id_map[name]
    return None


def _build_id_maps(connection):
    """Fetch port list and return (portnum_id_map, name_id_map)."""
    try:
        data = connection.send_request(None, 'ports')
        portnum_id_map = {}
        name_id_map = {}
        for port in data.get('ports', []):
            pid = port.get('id')
            if pid:
                pnum = port.get('portnum')
                if pnum is not None:
                    portnum_id_map[pnum] = pid
                pname = port.get('name')
                if pname:
                    name_id_map[pname] = pid
        return portnum_id_map, name_id_map
    except Exception:
        return {}, {}


def _build_command(port_id, command_val):
    """Build the API command for a single control action."""
    if command_val in _POWER_COMMANDS:
        return {
            'data': {'cmd': {'action': command_val}},
            'path': 'ports/' + port_id + '/power',
            'method': 'PUT',
        }
    return {
        'data': None,
        'path': 'ports/' + port_id + '/reset_counters',
        'method': 'POST',
    }


class PortsControl(ConfigBase):
    """
    Sends control actions (power on/off/cycle, tx/rx counter reset) to serial
    ports on Opengear devices.

    This is an action module — it is always considered changed when commands
    are issued. Use check mode to preview commands without sending them.
    """

    def __init__(self, module):
        super(PortsControl, self).__init__(module)

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = []

        portnum_id_map, name_id_map = _build_id_maps(self._connection)

        for entry in self._module.params['config']:
            entry = deepcopy(entry)
            port_id = _find_port_id(portnum_id_map, name_id_map, entry)
            command_val = entry.get('command')
            if not port_id or not command_val:
                continue
            commands.append(_build_command(port_id, command_val))

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
