# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.plugins.module_utils.utils import utils

# Session sub-fields to include in output
_SESSION_FIELDS = frozenset({"username", "client_pid"})


class PortsSessionsFacts(object):
    """
    Retrieves live pmshell session data for serial ports from Opengear devices.
    """

    def __init__(self, module, subspec=None, options=None):
        self._module = module

    def get_device_data(self, connection):
        return connection.get(None, 'ports')['ports']

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for ports_sessions.

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        objs = []
        for port in data:
            sessions = [
                {k: v for k, v in s.items() if k in _SESSION_FIELDS}
                for s in (port.get('sessions') or [])
            ]
            obj = {
                'id': port.get('id'),
                'name': port.get('name'),
                'portnum': port.get('portnum'),
                'sessions': sessions,
            }
            objs.append(utils.remove_empties(obj))

        ansible_facts['ansible_network_resources'].pop('ports_sessions', None)
        ansible_facts['ansible_network_resources']['ports_sessions'] = objs
        return ansible_facts
