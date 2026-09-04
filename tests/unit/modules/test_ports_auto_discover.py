# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import ports_auto_discover
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase

HAVE_SCHEDULE = {
    'enabled': False,
    'period': 'daily',
    'hour': 2,
    'minute': 0,
    'ports': [1, 2, 3],
}


class TestPortsAutoDiscoverModule(TestModuleBase):

    module = ports_auto_discover

    def setUp(self):
        super(TestPortsAutoDiscoverModule, self).setUp()
        self.maxDiff = None

        self.mock_connection = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "config.base.Connection"
        )
        self.connection = self.mock_connection.start()

        self.mock_get_data = patch(
            "ansible_collections.opengear.ng.plugins.module_utils."
            "facts.ports_auto_discover.PortsAutoDiscoverFacts._get_data"
        )
        self.get_data = self.mock_get_data.start()

    def tearDown(self):
        super(TestPortsAutoDiscoverModule, self).tearDown()
        self.mock_connection.stop()
        self.mock_get_data.stop()

    def load_fixtures(self, commands=None):
        discover_status = getattr(self, '_discover_status', 'idle')
        self.get_data.return_value = {
            'status': {'status': discover_status},
            'schedule': HAVE_SCHEDULE,
        }

        def send_request_side_effect(data, path, method=None):
            if data is None and path == 'ports/auto_discover/schedule':
                return {'auto_discover_schedule': HAVE_SCHEDULE}
            if data is None and path == 'ports/auto_discover':
                return {'auto_discover': {'status': discover_status}}
            return {}

        self.connection.return_value.send_request.side_effect = send_request_side_effect

    # --- gathered ---

    def test_gathered_returns_status_and_schedule(self):
        """gathered returns the current discovery status and schedule."""
        set_module_args({'state': 'gathered'})
        result = self.execute_module(changed=False)
        self.assertEqual(result['gathered']['status'], {'status': 'idle'})
        self.assertEqual(result['gathered']['schedule'], HAVE_SCHEDULE)

    # --- rendered ---

    def test_rendered_returns_schedule_without_contacting_device(self):
        """rendered builds the request body without any device access."""
        set_module_args({
            'config': {'schedule': {'enabled': True, 'period': 'daily', 'hour': 4}},
            'state': 'rendered',
        })
        result = self.execute_module(changed=False)
        self.assertEqual(
            result['rendered'],
            {'auto_discover_schedule': {'enabled': True, 'period': 'daily', 'hour': 4}},
        )
        self.connection.return_value.send_request.assert_not_called()

    # --- merged schedule ---

    def test_merged_schedule_change(self):
        """A partial schedule change is merged onto the device's current schedule."""
        set_module_args({
            'config': {'schedule': {'enabled': True}},
            'state': 'merged',
        })
        result = self.execute_module(changed=True)
        expected_target = dict(HAVE_SCHEDULE, enabled=True)
        self.assertEqual(result['commands'], [
            {
                'method': 'PUT',
                'path': 'ports/auto_discover/schedule',
                'data': {'auto_discover_schedule': expected_target},
            }
        ])

    def test_merged_schedule_idempotent(self):
        """No command is issued when the schedule already matches."""
        set_module_args({
            'config': {'schedule': dict(HAVE_SCHEDULE)},
            'state': 'merged',
        })
        self.execute_module(changed=False, commands=[])

    # --- replaced schedule ---

    def test_replaced_schedule_sends_only_specified_fields(self):
        """replaced sends exactly the provided schedule, not merged with have."""
        set_module_args({
            'config': {'schedule': {'enabled': True, 'period': 'weekly'}},
            'state': 'replaced',
        })
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            {
                'method': 'PUT',
                'path': 'ports/auto_discover/schedule',
                'data': {'auto_discover_schedule': {'enabled': True, 'period': 'weekly'}},
            }
        ])

    # --- trigger ---

    def test_trigger_all_ports(self):
        """An empty trigger dict discovers all ports."""
        set_module_args({'trigger': {}})
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            {
                'method': 'POST',
                'path': 'ports/auto_discover',
                'data': {'auto_discover': {'ports': None}},
            }
        ])

    def test_trigger_specific_ports_with_credentials(self):
        """Trigger options are passed through to the request body."""
        set_module_args({
            'trigger': {'ports': [1, 5], 'username': 'admin', 'password': 'secret'},
        })
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            {
                'method': 'POST',
                'path': 'ports/auto_discover',
                'data': {'auto_discover': {
                    'ports': [1, 5], 'username': 'admin', 'password': 'secret',
                }},
            }
        ])

    def test_trigger_check_mode_skips_post(self):
        """In check mode the trigger POST is not sent."""
        set_module_args({'_ansible_check_mode': True, 'trigger': {}})
        commands = [
            {
                'method': 'POST',
                'path': 'ports/auto_discover',
                'data': {'auto_discover': {'ports': None}},
            }
        ]
        self.execute_module(changed=True, commands=commands)
        self.connection.return_value.send_request.assert_not_called()

    # --- cancel ---

    def test_cancel_running_discovery(self):
        """cancel issues a DELETE when a discovery is currently running."""
        self._discover_status = 'running'
        set_module_args({'cancel': True})
        self.execute_module(changed=True, commands=[
            {'method': 'DELETE', 'path': 'ports/auto_discover', 'data': None}
        ])

    def test_cancel_idempotent_when_not_running(self):
        """cancel is a no-op when no discovery is running."""
        set_module_args({'cancel': True})
        self.execute_module(changed=False, commands=[])
