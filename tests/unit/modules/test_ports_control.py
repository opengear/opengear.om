# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import ports_control
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestPortsControlModule(TestModuleBase):

    module = ports_control

    def setUp(self):
        super(TestPortsControlModule, self).setUp()
        self.maxDiff = None

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestPortsControlModule, self).tearDown()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        ports = load_fixture("ports_config.cfg")

        def send_request_side_effect(data, path, method=None):
            if path == 'ports' and data is None:
                return {'ports': ports}
            return {}

        self.connection.return_value.send_request.side_effect = send_request_side_effect

    # --- power ---

    def test_power_command_resolves_by_portnum(self):
        """A port identified by portnum issues a power command to its id."""
        set_module_args({'config': [{'portnum': 1, 'command': 'cycle'}]})
        commands = [
            {'data': {'cmd': {'action': 'cycle'}}, 'path': 'ports/ports-1/power', 'method': 'PUT'}
        ]
        self.execute_module(changed=True, commands=commands)

    def test_power_command_resolves_by_name(self):
        """A port identified by name issues a power command to its id."""
        set_module_args({'config': [{'name': 'port02', 'command': 'off'}]})
        commands = [
            {'data': {'cmd': {'action': 'off'}}, 'path': 'ports/ports-2/power', 'method': 'PUT'}
        ]
        self.execute_module(changed=True, commands=commands)

    def test_power_command_resolves_by_id(self):
        """An explicit id is used directly without needing the port lookup."""
        set_module_args({'config': [{'id': 'ports-3', 'command': 'on'}]})
        commands = [
            {'data': {'cmd': {'action': 'on'}}, 'path': 'ports/ports-3/power', 'method': 'PUT'}
        ]
        self.execute_module(changed=True, commands=commands)

    def test_multiple_ports_power_commands(self):
        """Each entry in config produces its own power command."""
        set_module_args({
            'config': [
                {'portnum': 1, 'command': 'cycle'},
                {'portnum': 2, 'command': 'off'},
            ],
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 2)

    def test_unresolved_port_skipped(self):
        """A portnum that does not exist on the device produces no command."""
        set_module_args({'config': [{'portnum': 99, 'command': 'cycle'}]})
        self.execute_module(changed=False, commands=[])

    def test_check_mode_skips_power_put(self):
        """In check mode the power command is not sent, but is still reported."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': [{'portnum': 1, 'command': 'cycle'}],
        })
        commands = [
            {'data': {'cmd': {'action': 'cycle'}}, 'path': 'ports/ports-1/power', 'method': 'PUT'}
        ]
        self.execute_module(changed=True, commands=commands)
        # Only the port lookup GET should have been made - no PUT.
        self.assertEqual(self.connection.return_value.send_request.call_count, 1)

    # --- reset_counters ---

    def test_reset_counters_resolves_by_portnum(self):
        """reset_counters issues a POST with no body to the counters endpoint."""
        set_module_args({'config': [{'portnum': 1, 'command': 'reset_counters'}]})
        commands = [
            {'data': None, 'path': 'ports/ports-1/reset_counters', 'method': 'POST'}
        ]
        self.execute_module(changed=True, commands=commands)

    def test_reset_counters_unresolved_port_skipped(self):
        """A portnum that does not exist on the device produces no command."""
        set_module_args({'config': [{'portnum': 99, 'command': 'reset_counters'}]})
        self.execute_module(changed=False, commands=[])

    def test_check_mode_skips_reset_counters_post(self):
        """In check mode the reset_counters POST is not sent, but is still reported."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': [{'portnum': 1, 'command': 'reset_counters'}],
        })
        commands = [
            {'data': None, 'path': 'ports/ports-1/reset_counters', 'method': 'POST'}
        ]
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.connection.return_value.send_request.call_count, 1)

    def test_mixed_power_and_reset_counters_commands(self):
        """Power and reset_counters entries can be combined in one run."""
        set_module_args({
            'config': [
                {'portnum': 1, 'command': 'cycle'},
                {'portnum': 2, 'command': 'reset_counters'},
            ],
        })
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            {'data': {'cmd': {'action': 'cycle'}}, 'path': 'ports/ports-1/power', 'method': 'PUT'},
            {'data': None, 'path': 'ports/ports-2/reset_counters', 'method': 'POST'},
        ])
