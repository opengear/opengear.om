# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import pdu_control
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase, load_fixture


class TestPduControlModule(TestModuleBase):

    module = pdu_control

    def setUp(self):
        super(TestPduControlModule, self).setUp()
        self.maxDiff = None

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

    def tearDown(self):
        super(TestPduControlModule, self).tearDown()
        self.mock_connection.stop()

    def load_fixtures(self, commands=None):
        pdus = load_fixture("pdu_config.cfg")

        def send_request_side_effect(data, path, method=None):
            if path == 'pdus' and data is None:
                return {'pdus': pdus}
            return {}

        self.connection.return_value.send_request.side_effect = send_request_side_effect

    def test_action_resolves_by_name(self):
        """A PDU identified by name issues a PUT to its resolved id."""
        set_module_args({'config': [{'name': 'rack-pdu-01', 'outlets': [1], 'action': 'on'}]})
        commands = [
            {
                'data': {'pdu_outlets': {'outlets': [{'number': 1}], 'action': 'on'}},
                'path': 'pdus/pdus-1/outlets',
                'method': 'PUT',
            },
        ]
        self.execute_module(changed=True, commands=commands)

    def test_action_resolves_by_id(self):
        """An explicit id is used directly without needing the PDU lookup."""
        set_module_args({'config': [{'id': 'pdus-2', 'outlets': [1, 2], 'action': 'off'}]})
        commands = [
            {
                'data': {'pdu_outlets': {'outlets': [{'number': 1}, {'number': 2}], 'action': 'off'}},
                'path': 'pdus/pdus-2/outlets',
                'method': 'PUT',
            },
        ]
        self.execute_module(changed=True, commands=commands)

    def test_multiple_outlets_batched_into_one_command(self):
        """All outlets for one PDU/action combine into a single PUT."""
        set_module_args({'config': [{'name': 'rack-pdu-01', 'outlets': [1, 4, 8], 'action': 'cycle'}]})
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 1)
        self.assertEqual(
            result['commands'][0]['data']['pdu_outlets']['outlets'],
            [{'number': 1}, {'number': 4}, {'number': 8}],
        )

    def test_multiple_pdus_produce_multiple_commands(self):
        """Each entry in config produces its own command."""
        set_module_args({
            'config': [
                {'name': 'rack-pdu-01', 'outlets': [1], 'action': 'on'},
                {'name': 'rack-pdu-02', 'outlets': [2], 'action': 'off'},
            ],
        })
        result = self.execute_module(changed=True)
        self.assertEqual(len(result['commands']), 2)

    def test_unresolved_pdu_skipped(self):
        """A name that does not exist on the device produces no command."""
        set_module_args({'config': [{'name': 'does-not-exist', 'outlets': [1], 'action': 'on'}]})
        self.execute_module(changed=False, commands=[])

    def test_check_mode_skips_put(self):
        """In check mode the command is reported but never sent."""
        set_module_args({
            '_ansible_check_mode': True,
            'config': [{'name': 'rack-pdu-01', 'outlets': [1], 'action': 'cycle'}],
        })
        commands = [
            {
                'data': {'pdu_outlets': {'outlets': [{'number': 1}], 'action': 'cycle'}},
                'path': 'pdus/pdus-1/outlets',
                'method': 'PUT',
            },
        ]
        self.execute_module(changed=True, commands=commands)
        # Only the PDU lookup GET should have been made - no PUT.
        self.assertEqual(self.connection.return_value.send_request.call_count, 1)
