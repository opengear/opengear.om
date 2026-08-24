# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import failover
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestFailoverModule(TestModuleBase):

    module = failover

    def setUp(self):
        super(TestFailoverModule, self).setUp()
        self.maxDiff = None

        self.mock_get_device_data = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "facts.failover.FailoverFacts.get_device_data"
        )
        self.get_device_data = self.mock_get_device_data.start()

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestFailoverModule, self).tearDown()
        self.mock_get_device_data.stop()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture("failover_config.cfg")
        self.get_device_data.side_effect = load_from_file

    # ── Idempotency ──────────────────────────────────────────────────────────

    def test_failover_merged_idempotent(self):
        """No change when desired state already matches device."""
        set_module_args({
            'config': {
                'enabled': False,
                'probe_physif': 'net1',
                'probe_address': '8.8.8.8',
            },
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_failover_replaced_idempotent(self):
        """No change when replaced config is a subset of device state."""
        set_module_args({
            'config': {
                'enabled': False,
                'probe_physif': 'net1',
                'probe_address': '8.8.8.8',
                'probe_address_2': '1.1.1.1',
                'dormant_dns': False,
                'failover_physif': 'wwan0',
            },
            'state': 'replaced',
        })
        self.execute_module(changed=False, commands=[])

    # ── Merged state ─────────────────────────────────────────────────────────

    def test_failover_merged_enable(self):
        """Merged update enables failover and preserves unspecified fields."""
        set_module_args({
            'config': {
                'enabled': True,
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        cmd = result['commands'][0]
        self.assertEqual(cmd['method'], 'PUT')
        self.assertEqual(cmd['path'], 'failover/settings')
        body = cmd['data']['failover_settings']
        self.assertTrue(body['enabled'])
        # Unspecified fields should be preserved from device state
        self.assertEqual(body['probe_physif'], 'net1')
        self.assertEqual(body['probe_address'], '8.8.8.8')

    def test_failover_merged_update_probe_address_2(self):
        """Merged update sets secondary probe address."""
        set_module_args({
            'config': {
                'probe_address_2': '9.9.9.9',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['failover_settings']
        self.assertEqual(body['probe_address_2'], '9.9.9.9')
        # Primary probe address preserved
        self.assertEqual(body['probe_address'], '8.8.8.8')

    def test_failover_merged_dormant_dns(self):
        """Merged update sets dormant_dns flag."""
        set_module_args({
            'config': {
                'dormant_dns': True,
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['failover_settings']
        self.assertTrue(body['dormant_dns'])

    def test_failover_merged_failover_physif(self):
        """Merged update sets failover_physif."""
        set_module_args({
            'config': {
                'failover_physif': 'wwan1',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['failover_settings']
        self.assertEqual(body['failover_physif'], 'wwan1')

    def test_failover_merged_preserves_device_fields(self):
        """Merged sends a fully merged body so unspecified device fields are not lost."""
        set_module_args({
            'config': {
                'enabled': True,
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['failover_settings']
        # All device fields should appear in the merged body
        self.assertIn('probe_physif', body)
        self.assertIn('probe_address', body)
        self.assertIn('probe_address_2', body)
        self.assertIn('failover_physif', body)

    # ── Replaced / Overridden state ───────────────────────────────────────────

    def test_failover_replaced_sends_only_specified_fields(self):
        """Replaced sends exactly what is specified — no merging with device state."""
        set_module_args({
            'config': {
                'enabled': True,
                'probe_physif': 'net1',
                'probe_address': '1.2.3.4',
            },
            'state': 'replaced',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['failover_settings']
        self.assertEqual(body, {
            'enabled': True,
            'probe_physif': 'net1',
            'probe_address': '1.2.3.4',
        })
        # Device-only fields must NOT appear (no implicit merge)
        self.assertNotIn('probe_address_2', body)
        self.assertNotIn('failover_physif', body)

    def test_failover_overridden_same_as_replaced(self):
        """Overridden behaves identically to replaced for a singleton resource."""
        set_module_args({
            'config': {
                'enabled': True,
                'probe_physif': 'net2',
                'probe_address': '10.0.0.1',
            },
            'state': 'overridden',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.assertEqual(result['commands'][0]['method'], 'PUT')

    # ── Gathered / Rendered ──────────────────────────────────────────────────

    def test_failover_gathered(self):
        """Gathered state returns current failover config from device."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        self.assertIn('gathered', result)
        gathered = result['gathered']
        self.assertEqual(gathered['enabled'], False)
        self.assertEqual(gathered['probe_physif'], 'net1')
        self.assertEqual(gathered['probe_address'], '8.8.8.8')
        self.assertEqual(gathered['probe_address_2'], '1.1.1.1')
        self.assertEqual(gathered['dormant_dns'], False)
        self.assertEqual(gathered['failover_physif'], 'wwan0')

    def test_failover_rendered(self):
        """Rendered state generates commands without contacting the device."""
        set_module_args({
            'config': {
                'enabled': True,
                'probe_physif': 'net1',
                'probe_address': '8.8.8.8',
            },
            'state': 'rendered',
        })
        result = self.execute_module(changed=False)
        self.assertIn('rendered', result)
        self.get_device_data.assert_not_called()

    # ── Check mode ───────────────────────────────────────────────────────────

    def test_failover_check_mode(self):
        """Check mode generates commands but does not call send_request."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': {
                'enabled': True,
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.connection.return_value.send_request.assert_not_called()

    # ── Diff mode ────────────────────────────────────────────────────────────

    def test_failover_diff_merged_update(self):
        """Diff output shows before and after for a merged update."""
        set_module_args({
            '_ansible_diff': True,
            'config': {
                'enabled': True,
                'probe_address': '1.2.3.4',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertFalse(before['enabled'])
        self.assertTrue(after['enabled'])
        self.assertEqual(after['probe_address'], '1.2.3.4')

    def test_failover_no_diff_when_not_requested(self):
        """Diff key is absent when _ansible_diff is not set."""
        set_module_args({
            'config': {'enabled': True},
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertNotIn('diff', result)

    def test_failover_no_diff_when_idempotent(self):
        """Diff key is absent when there are no changes."""
        set_module_args({
            '_ansible_diff': True,
            'config': {
                'enabled': False,
                'probe_physif': 'net1',
                'probe_address': '8.8.8.8',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=False)
        self.assertNotIn('diff', result)

    def test_failover_check_mode_with_diff(self):
        """Check mode with diff generates diff without sending commands."""
        set_module_args({
            '_ansible_check_mode': True,
            '_ansible_diff': True,
            'config': {
                'enabled': True,
                'probe_address': '9.9.9.9',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.connection.return_value.send_request.assert_not_called()
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertFalse(before['enabled'])
        self.assertTrue(after['enabled'])
        self.assertEqual(after['probe_address'], '9.9.9.9')

    # ── commands key always present ───────────────────────────────────────────

    def test_failover_commands_always_present(self):
        """result['commands'] is always present, even when there are no changes."""
        set_module_args({
            'config': {
                'enabled': False,
                'probe_physif': 'net1',
                'probe_address': '8.8.8.8',
            },
            'state': 'merged',
        })
        result = self.execute_module(changed=False)
        self.assertIn('commands', result)
        self.assertEqual(result['commands'], [])
