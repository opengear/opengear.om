#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The om_failover class
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


class Failover(ConfigBase):
    """
    The om_failover class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'failover',
    ]

    def __init__(self, module):
        super(Failover, self).__init__(module)

    def get_failover_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        failover_facts = facts['ansible_network_resources'].get('failover')
        if not failover_facts:
            return []
        return failover_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_failover_facts = self.get_failover_facts()
        else:
            existing_failover_facts = {}
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_failover_facts))
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
            changed_failover_facts = self.get_failover_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        if self.state in self.ACTION_STATES:
            result['before'] = existing_failover_facts
            if result['changed']:
                result['after'] = changed_failover_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_failover_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_failover_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_failover_facts
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
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        commands.extend(Failover._state_overridden(want, have))
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = [{'data': {'failover_settings': want}, 'path': 'failover/settings', 'method': 'PUT'}]
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = remove_empties(want)
        have = remove_empties(have)
        if dict_diff(want, have):
            to_set = dict_merge(want, have)
            commands.append({'data': {'failover_settings': to_set}, 'path': 'failover/settings', 'method': 'PUT'})
        return commands
