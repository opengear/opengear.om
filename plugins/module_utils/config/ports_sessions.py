# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts


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


def _fetch_port_data(connection):
    """Fetch all ports and return (portnum_id_map, name_id_map, port_sessions_map)."""
    try:
        data = connection.send_request(None, 'ports')
        portnum_id_map = {}
        name_id_map = {}
        port_sessions_map = {}
        for port in data.get('ports', []):
            pid = port.get('id')
            if pid:
                pnum = port.get('portnum')
                if pnum is not None:
                    portnum_id_map[pnum] = pid
                pname = port.get('name')
                if pname:
                    name_id_map[pname] = pid
                sessions = port.get('sessions') or []
                port_sessions_map[pid] = [
                    s for s in sessions if s.get('client_pid') is not None
                ]
        return portnum_id_map, name_id_map, port_sessions_map
    except Exception:
        return {}, {}, {}


class PortsSessions(ConfigBase):
    """
    Terminates active pmshell sessions on serial ports on Opengear devices.

    Idempotent: if no matching sessions exist, no change is reported.
    Specific sessions can be targeted by client_pid; omitting client_pid
    terminates all sessions on the port.

    Also supports state=gathered, returning current session data per port
    without modifying device state.
    """

    gather_subset = ['!all', '!min']
    gather_network_resources = ['ports_sessions']

    def __init__(self, module):
        super(PortsSessions, self).__init__(module)

    def get_ports_sessions_facts(self):
        """Retrieve live port session facts from the device.

        :rtype: A list
        :returns: Current port session data as a list of dicts
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources
        )
        return facts['ansible_network_resources'].get('ports_sessions', [])

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}

        if self.state == 'gathered':
            result['gathered'] = self.get_ports_sessions_facts()
            return result

        commands = []

        portnum_id_map, name_id_map, port_sessions_map = _fetch_port_data(
            self._connection
        )

        for entry in self._module.params['config'] or []:
            entry = deepcopy(entry)
            port_id = _find_port_id(portnum_id_map, name_id_map, entry)
            if not port_id:
                continue

            current_sessions = port_sessions_map.get(port_id, [])
            wanted_pids = entry.get('client_pid') or []
            base_path = 'ports/' + port_id + '/sessions/'

            if wanted_pids:
                existing_pids = {s['client_pid'] for s in current_sessions}
                for pid in wanted_pids:
                    if pid in existing_pids:
                        commands.append({
                            'data': None,
                            'path': base_path + str(pid),
                            'method': 'DELETE',
                        })
            else:
                if current_sessions:
                    commands.append({
                        'data': None,
                        'path': base_path,
                        'method': 'DELETE',
                    })

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
