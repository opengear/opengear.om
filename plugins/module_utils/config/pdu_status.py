# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts


class PduStatus(ConfigBase):
    """
    Read-only module that gathers live PDU and outlet status data.
    """

    gather_subset = ['!all', '!min']
    gather_network_resources = ['pdu_status']

    def __init__(self, module):
        super(PduStatus, self).__init__(module)

    def get_pdu_status_facts(self):
        """Retrieve live PDU status facts from the device.

        :rtype: A list
        :returns: Current PDU status as a list of dicts
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources
        )
        return facts['ansible_network_resources'].get('pdu_status', [])

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        result['gathered'] = self.get_pdu_status_facts()
        return result
