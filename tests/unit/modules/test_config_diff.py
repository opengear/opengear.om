# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.tests.unit.compat.mock import patch
from ansible_collections.opengear.ng.plugins.modules import config_diff
from ansible_collections.opengear.ng.tests.unit.modules.utils import set_module_args
from .module_test_base import TestModuleBase

DIFF_OUTPUT = (
    "config --secrets=obfuscate merge physifs <<'END'\n"
    "-  physifs[0].description=\"1G Copper\"\n"
    "+  physifs[0].description=\"10G Copper\"\n"
    "END\n"
)

CONFIG_CONTENT = (
    "VERSION=\"25.11.6\"\n"
    "SKU=\"CM8148\"\n"
    "config --secrets=obfuscate merge physifs <<'END'\n"
    "  physifs[0].description=\"10G Copper\"\n"
    "END\n"
)


class TestConfigDiffModule(TestModuleBase):

    module = config_diff

    def setUp(self):
        super(TestConfigDiffModule, self).setUp()
        self.maxDiff = None

        self.mock_run_command = patch(
            'ansible.module_utils.basic.AnsibleModule.run_command'
        )
        self.run_command = self.mock_run_command.start()

    def tearDown(self):
        super(TestConfigDiffModule, self).tearDown()
        self.mock_run_command.stop()

    def load_fixtures(self, commands=None):
        # Default: write succeeds, diff finds differences, cleanup succeeds
        if not self.run_command.side_effect:    # only if not set by test
            self.run_command.side_effect = [
                (0, '', ''),                    # write succeeds
                (1, DIFF_OUTPUT, ''),           # diff found
                (0, '', ''),                    # cleanup
            ]

    # --- diff found ---
    def test_config_diff_changed(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=True)
        self.assertIn('diff', result)
        self.assertIn('prepared', result['diff'])
        self.assertEqual(result['diff']['prepared'], DIFF_OUTPUT)

    def test_config_diff_changed_contains_diff_markers(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=True)
        self.assertIn('-', result['diff']['prepared'])
        self.assertIn('+', result['diff']['prepared'])

    # --- no diff ---
    def test_config_diff_no_changes(self):
        self.run_command.side_effect = [
            (0, '', ''),   # write succeeds
            (0, '', ''),   # no diff
            (0, '', ''),   # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        result = self.execute_module(changed=False)
        self.assertNotIn('diff', result)

    # --- write fails ---
    def test_config_diff_write_fails(self):
        self.run_command.side_effect = [
            (1, '', 'permission denied'),  # write fails
            (0, '', ''),                   # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(failed=True)

    # --- diff command fails ---
    def test_config_diff_command_fails(self):
        self.run_command.side_effect = [
            (0, '', ''),              # write succeeds
            (2, '', 'syntax error'),  # diff command fails
            (0, '', ''),              # cleanup
        ]

        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(failed=True)

    # --- cleanup always runs ---
    def test_config_diff_cleanup_runs_on_success(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
        })

        self.execute_module(changed=True)
        calls = self.run_command.call_args_list
        cleanup_call = calls[-1]
        self.assertIn('rm', cleanup_call[0][0])

    def test_config_diff_cleanup_runs_on_failure(self):
        self.run_command.side_effect = [
            (0, '', ''),
            (2, '', 'syntax error'),
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
    def test_config_diff_custom_tmp_dir(self):
        set_module_args({
            'config_content': CONFIG_CONTENT,
            'remote_tmp_dir': '/var/tmp',
        })

        self.execute_module(changed=True)
        write_call = self.run_command.call_args_list[0]
        self.assertIn('/var/tmp', str(write_call))
