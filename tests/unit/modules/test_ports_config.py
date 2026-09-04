# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import ports_config
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestPortsConfigModule(TestModuleBase):

    module = ports_config

    def setUp(self):
        super(TestPortsConfigModule, self).setUp()
        self.maxDiff = None

        self.mock_get_device_data = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "facts.ports_config.PortsConfigFacts.get_device_data"
        )
        self.get_device_data = self.mock_get_device_data.start()

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestPortsConfigModule, self).tearDown()
        self.mock_get_device_data.stop()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture("ports_config.cfg")
        self.get_device_data.side_effect = load_from_file

    # ── Idempotency ──────────────────────────────────────────────────────────

    def test_ports_merged_idempotent_by_portnum(self):
        """No change when the desired config already matches the device (portnum)."""
        set_module_args({
            'config': [
                {
                    'portnum': 1,
                    'label': 'Port-1',
                    'mode': 'consoleServer',
                    'baudrate': '9600',
                    'databits': '8',
                    'stopbits': '1',
                    'parity': 'none',
                    'logging_level': 'disabled',
                    'single_session': False,
                    'raw_tcp': False,
                    'dtr_mode': 'alwayson',
                }
            ],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_ports_merged_idempotent_by_id(self):
        """No change when identified by explicit API id."""
        set_module_args({
            'config': [{'id': 'ports-2', 'baudrate': '115200', 'single_session': True}],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_ports_merged_idempotent_by_name(self):
        """No change when identified by system name."""
        set_module_args({
            'config': [{'name': 'port03', 'mode': 'localConsole', 'terminal_emulation': 'vt220'}],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_ports_replaced_idempotent(self):
        """Replaced is idempotent when specified fields already match."""
        set_module_args({
            'config': [
                {
                    'portnum': 2,
                    'label': 'switch-console',
                    'baudrate': '115200',
                    'single_session': True,
                }
            ],
            'state': 'replaced',
        })
        self.execute_module(changed=False, commands=[])

    # ── Merged state ─────────────────────────────────────────────────────────

    def test_ports_merged_update_label(self):
        """Merged update changes only the specified field."""
        set_module_args({
            'config': [{'portnum': 1, 'label': 'router-console'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        cmd = result['commands'][0]
        self.assertEqual(cmd['method'], 'PUT')
        self.assertEqual(cmd['path'], 'ports/ports-1')
        self.assertEqual(cmd['data']['port']['label'], 'router-console')
        # Merged: other fields must be carried over from device
        self.assertEqual(cmd['data']['port']['baudrate'], '9600')

    def test_ports_merged_update_baudrate(self):
        """Merged update sets a new baud rate."""
        set_module_args({
            'config': [{'portnum': 1, 'baudrate': '115200'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['port']
        self.assertEqual(body['baudrate'], '115200')

    def test_ports_merged_multiple_ports(self):
        """Merged can update more than one port in a single run."""
        set_module_args({
            'config': [
                {'portnum': 1, 'label': 'port-a'},
                {'portnum': 2, 'logging_level': 'eventsAndAllCharacters'},
            ],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 2)

    def test_ports_merged_control_code_partial(self):
        """Merged update on control_code merges only specified keys."""
        set_module_args({
            'config': [{'portnum': 4, 'control_code': {'quit': '~q'}}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['port']
        # Existing quit was '~.' — new value should be '~q'
        self.assertEqual(body['control_code']['quit'], '~q')

    def test_ports_merged_ip_alias(self):
        """Merged update can add an IP alias."""
        set_module_args({
            'config': [
                {
                    'portnum': 1,
                    'ip_alias': [{'ipaddress': '10.0.0.1', 'interface': 'net1'}],
                }
            ],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['port']
        self.assertEqual(body['ip_alias'], [{'ipaddress': '10.0.0.1', 'interface': 'net1'}])

    def test_ports_merged_ip_alias_idempotent(self):
        """Merged is idempotent when ip_alias already matches."""
        set_module_args({
            'config': [
                {
                    'portnum': 4,
                    'ip_alias': [{'ipaddress': '192.168.100.1', 'interface': 'net1'}],
                }
            ],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    def test_ports_merged_body_excludes_portnum(self):
        """The PUT body must not include identification fields."""
        set_module_args({
            'config': [{'portnum': 1, 'label': 'new-label'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['port']
        self.assertNotIn('id', body)
        self.assertNotIn('portnum', body)
        self.assertNotIn('name', body)

    def test_ports_merged_nonexistent_port_skipped(self):
        """Specifying a portnum that does not exist in have produces no command."""
        set_module_args({
            'config': [{'portnum': 99, 'label': 'ghost'}],
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    # ── Replaced state ───────────────────────────────────────────────────────

    def test_ports_replaced_behaves_like_merged(self):
        """Replaced merges onto the device's current value, same as merged.

        The device requires a complete port object on every PUT (it rejects
        a request missing e.g. 'parity'), so unspecified fields must be
        carried over from the device rather than omitted.
        """
        set_module_args({
            'config': [
                {
                    'portnum': 1,
                    'label': 'replaced-label',
                    'baudrate': '115200',
                }
            ],
            'state': 'replaced',
        })
        result = self.execute_module(changed=True)
        body = result['commands'][0]['data']['port']
        self.assertEqual(body['label'], 'replaced-label')
        self.assertEqual(body['baudrate'], '115200')
        # Unspecified fields must be carried over from the device
        self.assertEqual(body['mode'], 'consoleServer')
        self.assertEqual(body['parity'], 'none')

    def test_ports_replaced_path_is_correct(self):
        """Replaced command targets the correct port path."""
        set_module_args({
            'config': [{'portnum': 3, 'label': 'new-label'}],
            'state': 'replaced',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'][0]['path'], 'ports/ports-3')
        self.assertEqual(result['commands'][0]['method'], 'PUT')

    # ── Overridden state ─────────────────────────────────────────────────────

    def test_ports_overridden_equivalent_to_replaced(self):
        """Overridden behaves identically to replaced for serial ports."""
        set_module_args({
            'config': [{'portnum': 1, 'label': 'override-label'}],
            'state': 'overridden',
        })
        result_overridden = self.execute_module(changed=True)

        set_module_args({
            'config': [{'portnum': 1, 'label': 'override-label'}],
            'state': 'replaced',
        })
        result_replaced = self.execute_module(changed=True)

        self.assertEqual(result_overridden['commands'], result_replaced['commands'])

    # ── Gathered / Rendered ──────────────────────────────────────────────────

    def test_ports_gathered(self):
        """Gathered state returns all ports from device."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        self.assertIn('gathered', result)
        gathered = result['gathered']
        self.assertEqual(len(gathered), 4)
        portnums = [p['portnum'] for p in gathered]
        self.assertIn(1, portnums)
        self.assertIn(4, portnums)

    def test_ports_gathered_strips_readonly_fields(self):
        """Gathered facts do not include read-only API fields."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        for port in result['gathered']:
            self.assertNotIn('device', port)
            self.assertNotIn('status', port)
            self.assertNotIn('available_baudrates', port)
            self.assertNotIn('available_pinouts', port)
            self.assertNotIn('sessions', port)
            self.assertNotIn('pdu_outlets', port)

    def test_ports_gathered_includes_portnum(self):
        """Gathered facts include portnum for easy reference."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        for port in result['gathered']:
            self.assertIn('portnum', port)

    def test_ports_gathered_localconsole_fields(self):
        """Gathered facts include terminal_emulation for localConsole ports."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        port3 = next(p for p in result['gathered'] if p['portnum'] == 3)
        self.assertEqual(port3['mode'], 'localConsole')
        self.assertEqual(port3['terminal_emulation'], 'vt220')

    def test_ports_gathered_strips_empty_control_codes(self):
        """Gathered facts omit control_code when all values are empty."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        port1 = next(p for p in result['gathered'] if p['portnum'] == 1)
        # Port 1 has all-empty control_code — should be stripped by remove_empties
        self.assertNotIn('control_code', port1)

    def test_ports_gathered_retains_nonempty_control_codes(self):
        """Gathered facts include control_code when at least one key is set."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        port4 = next(p for p in result['gathered'] if p['portnum'] == 4)
        # Port 4 has quit='~.' set
        self.assertIn('control_code', port4)
        self.assertEqual(port4['control_code']['quit'], '~.')

    def test_ports_gathered_ip_alias(self):
        """Gathered facts include ip_alias entries."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        port4 = next(p for p in result['gathered'] if p['portnum'] == 4)
        self.assertEqual(port4['ip_alias'], [{'ipaddress': '192.168.100.1', 'interface': 'net1'}])

    def test_ports_rendered(self):
        """Rendered state generates commands without contacting the device."""
        set_module_args({
            'config': [{'portnum': 1, 'label': 'rendered-label'}],
            'state': 'rendered',
        })
        result = self.execute_module(changed=False)
        self.assertIn('rendered', result)

    # ── Check mode ───────────────────────────────────────────────────────────

    def test_ports_check_mode(self):
        """Check mode generates commands but does not send them."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': [{'portnum': 1, 'label': 'check-mode-label'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.connection.return_value.send_request.assert_not_called()

    # ── Diff mode ────────────────────────────────────────────────────────────

    def test_ports_diff_merged_update(self):
        """Diff output shows before and after for a merged update."""
        set_module_args({
            '_ansible_diff': True,
            'config': [{'portnum': 1, 'label': 'diff-label', 'baudrate': '115200'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertEqual(len(before), 1)
        self.assertEqual(before[0]['label'], 'Port-1')
        self.assertEqual(after[0]['label'], 'diff-label')
        self.assertEqual(after[0]['baudrate'], '115200')

    def test_ports_no_diff_when_not_requested(self):
        """Diff key is absent when _ansible_diff is not set."""
        set_module_args({
            'config': [{'portnum': 1, 'label': 'new-label'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.assertNotIn('diff', result)

    def test_ports_no_diff_when_idempotent(self):
        """Diff key is absent when there are no changes."""
        set_module_args({
            '_ansible_diff': True,
            'config': [{'portnum': 1, 'label': 'Port-1', 'baudrate': '9600'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=False)
        self.assertNotIn('diff', result)

    def test_ports_check_mode_with_diff(self):
        """Check mode combined with diff mode generates diff without sending."""
        set_module_args({
            '_ansible_check_mode': True,
            '_ansible_diff': True,
            'config': [{'portnum': 2, 'logging_level': 'eventsAndAllCharacters'}],
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        self.connection.return_value.send_request.assert_not_called()
        self.assertIn('diff', result)
        before = json.loads(result['diff']['before'])
        after = json.loads(result['diff']['after'])
        self.assertEqual(before[0]['logging_level'], 'eventsOnly')
        self.assertEqual(after[0]['logging_level'], 'eventsAndAllCharacters')
