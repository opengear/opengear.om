# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import config_import
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase

SUCCESS_OUTPUT = (
    "VERSION check passed\n"
    "SKU check passed\n"
    "import successful"
)

SKU_ERROR = (
    "import failed with the following error(s):\n"
    "Error detected during IMPORT operation when attempting to validate "
    "the contents. The SKU of the provided import file and the current "
    "SKU of the system do not match. To proceed with an unsupported import "
    "you may remove the 'SKU' line from the file and try again."
)

VALUE_ERROR = (
    "import failed with the following error(s):\n"
    "  Error:  Property 'power_alert_group.power_supply_voltage_alert.millivolt_lower'"
    " is out of range 8000 to 16000\n"
    "Type 'ogcli help monitoring/alerts/power' for examples specific to this entity."
)

CONFIG_CONTENT = (
    "VERSION=\"25.11.6\"\n"
    "SKU=\"CM8148\"\n"
    "config --secrets=obfuscate merge physifs <<'END'\n"
    "  physifs[0].description=\"1G Copper\"\n"
    "END\n"
)


class TestConfigImportModule(TestModuleBase):

    module = config_import

    def setUp(self):
        super(TestConfigImportModule, self).setUp()
        self.maxDiff = None

        self.mock_run_command = patch(
            'ansible.module_utils.basic.AnsibleModule.run_command'
        )
        self.run_command = self.mock_run_command.start()

    def tearDown(self):
        super(TestConfigImportModule, self).tearDown()
        self.mock_run_command.stop()

    def load_fixtures(self, commands=None):
        if not self.run_command.side_effect:
            self.run_command.side_effect = [
                (0, '', ''),              # write succeeds
                (0, SUCCESS_OUTPUT, ''),  # import succeeds
                (0, '', ''),              # cleanup
            ]

    # --- import succeeds ---
    def test_config_import_success(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=True)
        self.assertIn('msg', result)
        self.assertIn('import successful', result['msg'])

    def test_config_import_success_msg_contains_checks(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=True)
        self.assertIn('VERSION check passed', result['msg'])
        self.assertIn('SKU check passed', result['msg'])

    # --- check mode ---
    def test_config_import_check_mode(self):
        set_module_args({
            '_ansible_check_mode': True,
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=True)
        self.run_command.assert_not_called()

    # --- write fails ---
    def test_config_import_write_fails(self):
        self.run_command.side_effect = [
            (1, '', 'permission denied'),  # write fails
            (0, '', ''),                   # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(failed=True)

    # --- import fails ---
    def test_config_import_sku_mismatch(self):
        self.run_command.side_effect = [
            (0, '', ''),           # write succeeds
            (1, '', SKU_ERROR),    # import fails - sku mismatch
            (0, '', ''),           # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(failed=True)
        self.assertIn('SKU', result['msg'])

    def test_config_import_value_error(self):
        self.run_command.side_effect = [
            (0, '', ''),            # write succeeds
            (1, '', VALUE_ERROR),   # import fails - value out of range
            (0, '', ''),            # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(failed=True)
        self.assertIn('out of range', result['msg'])

    # --- cleanup always runs ---
    def test_config_import_cleanup_runs_on_success(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(changed=True)
        calls = self.run_command.call_args_list
        cleanup_call = calls[-1]
        self.assertIn('rm', cleanup_call[0][0])

    def test_config_import_cleanup_runs_on_failure(self):
        self.run_command.side_effect = [
            (0, '', ''),
            (1, '', SKU_ERROR),
            (0, '', ''),
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(failed=True)
        calls = self.run_command.call_args_list
        cleanup_call = calls[-1]
        self.assertIn('rm', cleanup_call[0][0])

    # --- custom remote_tmp_dir ---
    def test_config_import_custom_tmp_dir(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
            'remote_tmp_dir': '/var/tmp',
        })

        self.execute_module(changed=True)
        write_call = self.run_command.call_args_list[0]
        self.assertIn('/var/tmp', str(write_call))
