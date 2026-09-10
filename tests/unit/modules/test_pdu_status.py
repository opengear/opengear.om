# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import pdu_status
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestPduStatusModule(TestModuleBase):

    module = pdu_status

    def setUp(self):
        super(TestPduStatusModule, self).setUp()
        self.maxDiff = None

        self.mock_get_device_data = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "facts.pdu_status.PduStatusFacts.get_device_data"
        )
        self.get_device_data = self.mock_get_device_data.start()

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestPduStatusModule, self).tearDown()
        self.mock_get_device_data.stop()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        self.get_device_data.return_value = load_fixture("pdu_config.cfg")

    def test_gathered_returns_all_pdus(self):
        """Gathered status includes every PDU on the device."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        self.assertEqual(len(result['gathered']), 3)

    def test_gathered_includes_core_identity_fields(self):
        """Each entry surfaces id, name, driver, method, monitor, outlet_count."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        self.assertEqual(pdu1['id'], 'pdus-1')
        self.assertEqual(pdu1['driver'], {'id': 'servertech', 'name': 'Servertech driver'})
        self.assertEqual(pdu1['method'], 'snmp')
        self.assertEqual(pdu1['monitor'], True)
        self.assertEqual(pdu1['outlet_count'], 2)

    def test_gathered_outlets_include_status_and_last_action(self):
        """Outlet entries surface live status and last action details."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        outlet1 = next(o for o in pdu1['outlets'] if o['number'] == 1)
        self.assertEqual(outlet1['id'], 'outlets-1')
        self.assertEqual(outlet1['status'], 'on')
        self.assertEqual(outlet1['last_action'], 'on')
        self.assertIn('status_timestamp', outlet1)
        self.assertIn('last_action_timestamp', outlet1)

    def test_gathered_monitor_false_retained(self):
        """A monitor value of false is retained, not stripped as empty."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu3 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-03')
        self.assertEqual(pdu3['monitor'], False)

    def test_gathered_never_changes_device(self):
        """This module never reports changed, regardless of device state."""
        set_module_args({'state': 'gathered'})
        self.execute_module(changed=False)
        self.connection.return_value.send_request.assert_not_called()
