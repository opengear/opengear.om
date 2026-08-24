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
    dict_merge,
    is_subset,
    remove_empties,
    to_list,
)


class Failover(ConfigBase):
    """
    Manages configuration of failover behavior on Opengear devices
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
        self.current_state = {}

    def get_failover_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data
        )
        failover_facts = facts['ansible_network_resources'].get('failover')
        if not failover_facts:
            return {}
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
            commands.extend(self.set_config(existing_failover_facts, warnings))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    try:
                        self._connection.send_request(
                            command['data'], command['path'], command['method']
                        )
                    except ConnectionError as exc:
                        if not exc.args[0].startswith('Expecting value:'):
                            raise exc
            else:
                # Simulate state changes for check mode so result['after'] is accurate
                self.current_state = deepcopy(existing_failover_facts)
                for command in commands:
                    self.current_state.update(command['data']['failover_settings'])
            result['changed'] = True

        result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            if result['changed'] and self._module.check_mode:
                # Use simulated state; device state is unchanged in check mode
                changed_failover_facts = self.get_failover_facts(self.current_state or None)
            else:
                changed_failover_facts = self.get_failover_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands

        if self.state in self.ACTION_STATES:
            result['before'] = existing_failover_facts
            if result['changed']:
                result['after'] = changed_failover_facts
                if self._module._diff:
                    # Compute diff from command body so it is accurate in both
                    # check mode and real mode
                    cmd_body = commands[0]['data']['failover_settings'] if commands else {}
                    diff_after = dict_merge(deepcopy(existing_failover_facts), cmd_body)
                    result['diff'] = {
                        'before': json.dumps(existing_failover_facts, indent=4) + '\n',
                        'after': json.dumps(diff_after, indent=4) + '\n',
                    }
        elif self.state == 'gathered':
            result['gathered'] = changed_failover_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_failover_facts, warnings):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_failover_facts
        resp = self.set_state(want, have, warnings)
        return to_list(resp)

    def set_state(self, want, have, warnings):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state in ('overridden', 'replaced'):
            commands = self._state_replaced(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        else:
            commands = []
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced or overridden.

        Sends exactly the specified config without merging with device state.

        :rtype: A list
        :returns: the commands necessary to set the desired configuration
        """
        commands = []
        want = remove_empties(want or {})
        have = remove_empties(have or {})
        if is_subset(want, have):
            return commands
        commands.append({
            'data': {'failover_settings': want},
            'path': 'failover/settings',
            'method': 'PUT',
        })
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged.

        Deep-merges want into the device state so unspecified fields are preserved.

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = remove_empties(want or {})
        have = remove_empties(have or {})
        if is_subset(want, have):
            return commands
        merged = dict_merge(have, want)
        commands.append({
            'data': {'failover_settings': merged},
            'path': 'failover/settings',
            'method': 'PUT',
        })
        return commands
