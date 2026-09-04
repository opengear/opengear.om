# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.plugins.module_utils.utils import utils


class PortsStatusFacts(object):
    """
    Retrieves live port status data from Opengear devices.
    """

    def __init__(self, module, subspec=None, options=None):
        self._module = module

    def get_device_data(self, connection):
        return connection.get(None, 'ports')['ports']

    def get_pin_status_data(self, connection):
        return connection.get(None, 'ports/ports_status')['port_status']

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for ports_status.

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        pin_status_by_id = {
            p['id']: p for p in self.get_pin_status_data(connection) if p.get('id')
        }

        objs = []
        for port in data:
            pin_status = pin_status_by_id.get(port.get('id'), {})
            obj = {
                'id': port.get('id'),
                'name': port.get('name'),
                'portnum': port.get('portnum'),
                'label': port.get('label'),
                'mode': port.get('mode'),
                'device': port.get('device'),
                'status': port.get('status'),
                'rts': pin_status.get('rts'),
                'cts': pin_status.get('cts'),
                'dtr': pin_status.get('dtr'),
                'dsr': pin_status.get('dsr'),
                'dcd': pin_status.get('dcd'),
                'tx': pin_status.get('tx'),
                'rx': pin_status.get('rx'),
                'pdu_outlets': port.get('pdu_outlets') or [],
            }
            objs.append(utils.remove_empties(obj))

        ansible_facts['ansible_network_resources'].pop('ports_status', None)
        ansible_facts['ansible_network_resources']['ports_status'] = objs
        return ansible_facts
