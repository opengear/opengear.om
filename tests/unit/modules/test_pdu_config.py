# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import pdu_config
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestPduConfigModule(TestModuleBase):

    module = pdu_config

    def setUp(self):
        super(TestPduConfigModule, self).setUp()
        self.maxDiff = None

        self.mock_get_device_data = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "facts.pdu_config.PduConfigFacts.get_device_data"
        )
        self.get_device_data = self.mock_get_device_data.start()

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestPduConfigModule, self).tearDown()
        self.mock_get_device_data.stop()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        self.get_device_data.return_value = load_fixture("pdu_config.cfg")

    # --- gathered ---

    def test_gathered_returns_all_pdus(self):
        """Gathered config includes every PDU on the device."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        self.assertEqual(len(result['gathered']), 3)

    def test_gathered_driver_is_an_object(self):
        """driver is surfaced as an id/name object, not a flat string."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        self.assertEqual(pdu1['driver'], {'id': 'servertech', 'name': 'Servertech driver'})

    def test_gathered_snmp_uses_security_name_not_username(self):
        """snmp surfaces security_name (per the RAML), not a bogus username field."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        self.assertEqual(pdu1['snmp']['security_name'], 'admin')
        self.assertNotIn('username', pdu1['snmp'])

    def test_gathered_outlets_exclude_status_fields(self):
        """Outlet entries surface only name/port/number - status data belongs to pdu_status."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        self.assertEqual(
            pdu1['outlets'],
            [
                {'number': 1, 'name': 'web-server-1', 'port': 'serial/by-opengear-id/port07'},
                {'number': 2, 'name': 'web-server-2', 'port': 'serial/by-opengear-id/port08'},
            ],
        )

    def test_gathered_excludes_outlet_count(self):
        """outlet_count is read-only and is not part of pdu_config."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        pdu1 = next(p for p in result['gathered'] if p['name'] == 'rack-pdu-01')
        self.assertNotIn('outlet_count', pdu1)

    # --- merged ---

    def test_merged_idempotent(self):
        """No change when desired state already matches device."""
        set_module_args({
            'config': [{'name': 'rack-pdu-01', 'monitor': True, 'method': 'snmp'}],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_merged_updates_existing_pdu_by_name(self):
        """A changed field produces a PUT with a fully cleaned body."""
        set_module_args({
            'config': [{'name': 'rack-pdu-02', 'monitor': False}],
            'state': 'merged',
        })
        commands = [
            {
                'data': {
                    'pdu': {
                        'name': 'rack-pdu-02',
                        'driver': {'id': 'apcpdu4'},
                        'monitor': False,
                        'method': 'powerman',
                        'powerman': {
                            'username': 'admin',
                            'password': 'password',
                            'port': 'serial/by-opengear-id/port01',
                        },
                        'outlets': [
                            {'number': 1, 'name': 'apc outlet 1', 'port': 'serial/by-opengear-id/port08'},
                            {'number': 2, 'name': 'apc outlet 2', 'port': 'serial/by-opengear-id/port09'},
                        ],
                    },
                },
                'path': 'pdus/pdus-2',
                'method': 'PUT',
            },
        ]
        self.execute_module(changed=True, commands=commands)

    def test_merged_updates_by_id(self):
        """Identify the PDU by id when name is not provided."""
        set_module_args({
            'config': [{'id': 'pdus-3', 'monitor': True}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.assertEqual(result['commands'][0]['method'], 'PUT')
        self.assertEqual(result['commands'][0]['path'], 'pdus/pdus-3')
        self.assertNotIn('id', result['commands'][0]['data']['pdu'])

    def test_merged_strips_nested_ids_and_driver_name(self):
        """Device-assigned nested ids and the read-only driver name are never sent."""
        set_module_args({
            'config': [{'name': 'rack-pdu-01', 'monitor': False}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['pdu']
        self.assertEqual(body['driver'], {'id': 'servertech'})
        self.assertNotIn('id', body['snmp'])

    def test_merged_replaces_outlets_wholesale(self):
        """Providing outlets replaces the full list rather than merging by number."""
        set_module_args({
            'config': [{
                'name': 'rack-pdu-01',
                'outlets': [{'number': 1, 'name': 'renamed-outlet'}],
            }],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['pdu']
        self.assertEqual(body['outlets'], [{'number': 1, 'name': 'renamed-outlet', 'port': None}])

    def test_merged_new_pdu_posts(self):
        """A PDU with no matching name triggers a POST with no id in the path."""
        set_module_args({
            'config': [{
                'name': 'rack-pdu-04',
                'method': 'shell',
                'driver': {'id': 'apc_pdu'},
                'shell': {'username': 'admin', 'password': 'secret', 'port': 'ports-9'},
            }],
            'state': 'merged',
        })
        commands = [
            {
                'data': {
                    'pdu': {
                        'name': 'rack-pdu-04',
                        'method': 'shell',
                        'driver': {'id': 'apc_pdu'},
                        'shell': {'username': 'admin', 'password': 'secret', 'port': 'ports-9'},
                    },
                },
                'path': 'pdus/',
                'method': 'POST',
            },
        ]
        self.execute_module(changed=True, commands=commands)

    def test_check_mode_skips_put(self):
        """In check mode the command is reported but never sent."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': [{'name': 'rack-pdu-02', 'monitor': False}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.connection.return_value.send_request.assert_not_called()

    # --- replaced ---

    def test_replaced_behaves_like_merged(self):
        """replaced delegates to merged - the device rejects partial PUT bodies."""
        set_module_args({
            'config': [{'name': 'rack-pdu-02', 'monitor': False}],
            'state': 'replaced',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'][0]['method'], 'PUT')
        self.assertEqual(result['commands'][0]['data']['pdu']['monitor'], False)

    # --- deleted ---

    def test_deleted_by_name(self):
        """A named PDU is deleted by its resolved id."""
        set_module_args({
            'config': [{'name': 'rack-pdu-03'}],
            'state': 'deleted',
        })
        commands = [
            {'data': None, 'path': 'pdus/pdus-3', 'method': 'DELETE'},
        ]
        self.execute_module(changed=True, commands=commands)

    # --- overridden ---

    def test_overridden_deletes_unlisted_pdus(self):
        """PDUs not present in want are deleted; the listed PDU is left alone."""
        set_module_args({
            'config': [{'name': 'rack-pdu-01', 'monitor': True, 'method': 'snmp'}],
            'state': 'overridden',
        })
        commands = [
            {'data': None, 'path': 'pdus/pdus-2', 'method': 'DELETE'},
            {'data': None, 'path': 'pdus/pdus-3', 'method': 'DELETE'},
        ]
        self.execute_module(changed=True, commands=commands)

    # --- diff mode ---

    def test_diff_merged_update(self):
        """Diff output shows before and after for a merged update."""
        set_module_args({
            '_ansible_diff': True,
            'config': [{'name': 'rack-pdu-02', 'monitor': False}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertEqual(len(before), 1)
        self.assertEqual(before[0]['monitor'], True)
        self.assertEqual(after[0]['monitor'], False)

    def test_no_diff_when_not_requested(self):
        """Diff key is absent when _ansible_diff is not set."""
        set_module_args({
            'config': [{'name': 'rack-pdu-02', 'monitor': False}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertNotIn('diff', result)

    def test_no_diff_when_idempotent(self):
        """Diff key is absent when there are no changes."""
        set_module_args({
            '_ansible_diff': True,
            'config': [{'name': 'rack-pdu-01', 'monitor': True, 'method': 'snmp'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=False)
        self.assertNotIn('diff', result)

    def test_check_mode_with_diff(self):
        """Check mode combined with diff mode generates diff without sending."""
        set_module_args({
            '_ansible_check_mode': True,
            '_ansible_diff': True,
            'config': [{'name': 'rack-pdu-03', 'monitor': True}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.connection.return_value.send_request.assert_not_called()
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertEqual(before[0]['monitor'], False)
        self.assertEqual(after[0]['monitor'], True)
