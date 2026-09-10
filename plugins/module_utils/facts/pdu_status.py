# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.plugins.module_utils.utils import utils

_OUTLET_FIELDS = (
    "id", "number", "name", "port",
    "status", "status_timestamp", "last_action", "last_action_timestamp",
)


class PduStatusFacts(object):
    """
    Retrieves live PDU and outlet status data from Opengear devices.
    """

    def __init__(self, module, subspec=None, options=None):
        self._module = module

    def get_device_data(self, connection):
        return connection.get(None, 'pdus')['pdus']

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for pdu_status.

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        objs = []
        for pdu in data:
            driver = pdu.get('driver') or {}
            outlets = [
                utils.remove_empties({field: outlet.get(field) for field in _OUTLET_FIELDS})
                for outlet in (pdu.get('outlets') or [])
            ]
            obj = {
                'id': pdu.get('id'),
                'name': pdu.get('name'),
                'driver': utils.remove_empties({
                    'id': driver.get('id'),
                    'name': driver.get('name'),
                }),
                'method': pdu.get('method'),
                'monitor': pdu.get('monitor'),
                'outlet_count': pdu.get('outlet_count'),
                'outlets': outlets,
            }
            objs.append(utils.remove_empties(obj))

        ansible_facts['ansible_network_resources'].pop('pdu_status', None)
        ansible_facts['ansible_network_resources']['pdu_status'] = objs
        return ansible_facts
