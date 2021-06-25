#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_ports class
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
    remove_empties,
    dict_merge,
)
from ansible_collections.opengear.om.plugins.module_utils.network.om.facts.facts import Facts

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.om.plugins.module_utils.network.om.utils.utils import (
    command_builder,
    find_instance_id,
    is_subset,
)


class Ports(ConfigBase):
    """
    The om_ports class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'ports',
    ]

    def __init__(self, module):
        super(Ports, self).__init__(module)

    def get_ports_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        ports_facts = facts['ansible_network_resources'].get('ports')
        if not ports_facts:
            return []
        return ports_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_ports_facts = self.get_ports_facts()
        else:
            existing_ports_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_ports_facts))
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
            changed_ports_facts = self.get_ports_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_ports_facts
            if result['changed']:
                result['after'] = changed_ports_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_ports_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_ports_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_ports_facts
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

        id_port_map = {}
        for port in have['ports']:
            id_port_map[port['id']] = port

        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, id_port_map, have['auto_discover'])
        elif state == 'deleted':
            commands = self._state_deleted(want['ports'])
        elif state == 'merged':
            commands = self._state_merged(want, id_port_map, have['auto_discover'])
        elif state == 'replaced':
            commands = self._state_replaced(want, id_port_map, have['auto_discover'])
        return commands

    @staticmethod
    def _state_replaced(want, id_port_map, auto_discover):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want = remove_empties(want)
        for port in want['ports']:
            port_id = port['id']
            if port_id in id_port_map:
                current_port = id_port_map[port_id]
                current_sessions = current_port.pop('sessions', None)
                wanted_sessions = port.pop('sessions', None)
                power = port.pop('power', None)
                if 'mode' in port:
                    if port['mode'] != 'consoleServer':
                        port.pop('escape_char', None)
                        port.pop('ip_alias', None)
                    if port['mode'] != 'localConsole':
                        port.pop('terminal_emulation', None)
                        port.pop('kernel_debug', None)
                if remove_empties(port) == remove_empties(current_port):
                    continue
                command = command_builder({'port': port}, 'ports/', port_id)
                if command:
                    commands.append(command)
                if power:
                    command = command_builder({'cmd': power}, 'ports/', port_id + '/power')
                    if command:
                        commands.append(command)
                #
                # unwanted_session_pids = []
                # for session in current_sessions:
                #     unwanted_session_pids.append(session['pid'])
                # remove_all = True
                # for session in wanted_sessions:
                #     if session['pid'] in unwanted_session_pids:
                #         unwanted_session_pids.remove(session['pid'])
                #         remove_all = False
        if 'auto_discover' in want:
            path = 'ports/auto_discover'
            ports = None
            if 'ports' in want['auto_discover']:
                ports = want['auto_discover']['ports']
                if isinstance(ports, list):
                    ports.sort()
            if 'schedule' in want['auto_discover']:
                if 'ports' in auto_discover and isinstance(auto_discover['ports'], list):
                    auto_discover['ports'].sort()
                if 'period' in want['auto_discover']['schedule']:
                    if want['auto_discover']['schedule']['period'] != 'weekly':
                        want['auto_discover']['schedule'].pop('day_of_week', None)
                    if want['auto_discover']['schedule']['period'] != 'monthly':
                        want['auto_discover']['schedule'].pop('day_of_month', None)
                if auto_discover['ports'] != ports \
                        or dict_diff(auto_discover['schedule'], want['auto_discover']['schedule']):
                    want['auto_discover']['schedule']['ports'] = ports
                    command = command_builder({'auto_discover_schedule': want['auto_discover']['schedule']}, path,
                                              '/schedule')
                    if command:
                        commands.append(command)
            if 'start' in want['auto_discover'] and want['auto_discover']['start']:
                command = command_builder({'auto_discover': {'ports': ports}}, path)
                if command:
                    commands.append(command)
        return commands

    @staticmethod
    def _state_overridden(want, id_port_map, auto_discover):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        commands.extend(Ports._state_replaced(want, id_port_map, auto_discover))
        return commands

    @staticmethod
    def _state_merged(want, id_port_map, auto_discover):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = remove_empties(want)
        for port in want['ports']:
            port_id = port['id']
            if port_id in id_port_map:
                current_port = remove_empties(id_port_map[port_id])
                current_port.pop('sessions', None)
                port.pop('sessions', None)
                power = port.pop('power', None)
                if is_subset(port, current_port):
                    continue
                else:
                    data = dict_merge(current_port, port)
                command = command_builder({'port': data}, 'ports/', port_id)
                if command:
                    commands.append(command)
                if power:
                    command = command_builder({'cmd': power}, 'ports/', port_id + '/power')
                    if command:
                        commands.append(command)
                #
                # unwanted_session_pids = []
                # for session in current_sessions:
                #     unwanted_session_pids.append(session['pid'])
                # remove_all = True
                # for session in wanted_sessions:
                #     if session['pid'] in unwanted_session_pids:
                #         unwanted_session_pids.remove(session['pid'])
                #         remove_all = False
        if 'auto_discover' in want:
            path = 'ports/auto_discover'
            ports = None
            if 'ports' in want['auto_discover']:
                ports = want['auto_discover']['ports']
            if 'schedule' in want['auto_discover']:
                if not ports and auto_discover['ports']:
                    ports = auto_discover['ports']
                want['auto_discover']['schedule']['ports'] = ports
                command = command_builder({'auto_discover_schedule': want['auto_discover']['schedule']}, path,
                                          '/schedule')
                if command:
                    commands.append(command)
            if 'start' in want['auto_discover'] and want['auto_discover']['start']:
                command = command_builder({'auto_discover': ports}, path)
                if command:
                    commands.append(command)
        return commands

    @staticmethod
    def _state_deleted(want):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for port in want:
            port_id = port['id']
            path = 'ports/' + port_id
            if port['sessions']:
                for session in port['sessions']:
                    command = command_builder(None, path, '/sessions/' + session['client_pid'])
                    if command:
                        commands.add(command)
            else:
                command = command_builder(None, path, '/sessions/')
                if command:
                    commands.add(command)
        return commands
