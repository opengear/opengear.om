# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

_TRIGGER_PATH = 'ports/auto_discover'
_SCHEDULE_PATH = 'ports/auto_discover/schedule'


class PortsAutoDiscoverFacts(object):
    """
    Retrieves Port Auto-Discovery status and schedule from Opengear devices.
    """

    def __init__(self, module, subspec=None, options=None):
        self._module = module

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for ports_auto_discover.

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self._get_data(connection)

        ansible_facts['ansible_network_resources'].pop('ports_auto_discover', None)
        ansible_facts['ansible_network_resources']['ports_auto_discover'] = data
        return ansible_facts

    def _get_data(self, connection):
        try:
            status_resp = connection.send_request(None, _TRIGGER_PATH)
            status = status_resp.get('auto_discover') or {}
        except Exception:
            status = {}
        try:
            schedule_resp = connection.send_request(None, _SCHEDULE_PATH)
            schedule = schedule_resp.get('auto_discover_schedule') or {}
        except Exception:
            schedule = {}
        return {'status': status, 'schedule': schedule}
