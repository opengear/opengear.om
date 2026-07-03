#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: config_diff
version_added: '1.0.0'
short_description: Diff device configuration on Opengear devices
description:
  - Compares the current device configuration against a provided configuration
    and returns the differences in dotnotation format.
  - The provided configuration content is written to a temporary file on the
    device, compared using the C(config diff) command, and removed after comparison.
author:
  - Opengear (@opengear)
options:
  config_content:
    description:
      - The configuration content in dotnotation format to diff against the
        current device configuration. Use the C(lookup) plugin or
        C(config_export) module to obtain this content.
    type: str
    required: true
  remote_tmp_dir:
    description:
      - Temporary directory on the device to store the config file during comparison.
    type: str
    default: /tmp
notes:
  - "This module requires `ansible_connection: ssh` to be set for the task or host. It cannot use the httpapi connection plugin."
  - The user must have admin access on the device.
  - C(changed) is true when differences are found between the current configuration and the provided content.
  - Use the C(lookup) plugin to read a local file into C(config_content).
"""

EXAMPLES = """
- name: Export current device configuration
  opengear.ng.config_export:
    state: gathered
  register: export_result

- name: Save configuration to file
  ansible.builtin.copy:
    content: "{{ export_result.gathered }}"
    dest: "/tmp/device-config.cfg"
    mode: '0644'
  delegate_to: localhost

# Make changes to /tmp/device-config.cfg here

- name: Diff modified configuration against device
  opengear.ng.config_diff:
    config_content: "{{ lookup('file', '/tmp/device-config.cfg') }}"
  vars:
    ansible_connection: ssh
  register: diff_result

- name: No differences found
  ansible.builtin.debug:
    msg: "Configuration matches device — no differences found."
  when: not diff_result.changed

- name: Save diff to file
  ansible.builtin.copy:
    content: "{{ diff_result.diff.prepared }}"
    dest: "/tmp/config-diff-result.txt"
    mode: '0644'
  delegate_to: localhost
  when: diff_result.changed

- name: Show diff
  ansible.builtin.command:
    cmd: "cat /tmp/config-diff-result.txt"
  delegate_to: localhost
  when: diff_result.changed
  register: cat_result
  changed_when: false

- name: Print diff
  ansible.builtin.debug:
    msg: "{{ cat_result.stdout_lines }}"
  when: diff_result.changed
"""

RETURN = """
changed:
  description: True if differences were found between the device configuration and the provided content.
  returned: always
  type: bool
diff:
  description: The differences between the current device configuration and the provided content.
  returned: when changed
  type: dict
  contains:
    prepared:
      description: Diff output in dotnotation format.
      type: str
"""

import os

from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    argument_spec = {
        'config_content': {
            'type': 'str',
            'required': True,
            'no_log': False,
        },
        'remote_tmp_dir': {
            'type': 'str',
            'default': '/tmp',
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    config_content = module.params['config_content']
    remote_tmp_dir = module.params['remote_tmp_dir']
    remote_path = os.path.join(remote_tmp_dir, f"ansible_config_diff_{os.getpid()}.cfg")

    result = {'changed': False}

    try:
        # Write config content to temp file on device
        write_rc, write_stdout, write_stderr = module.run_command(
            ['bash', '-c', f"cat > {remote_path}"],
            data=config_content,
        )
        if write_rc != 0:
            module.fail_json(
                msg=f"Failed to write config content to device: {write_stderr}"
            )

        # Run config diff on the device
        diff_rc, diff_stdout, diff_stderr = module.run_command(
            ['config', 'diff', remote_path]
        )

        # exit code 1 means differences found, 0 means no differences
        if diff_rc > 1:
            module.fail_json(
                msg=f"config diff failed: {diff_stderr}",
                rc=diff_rc,
            )

        if diff_rc == 1:
            result['changed'] = True
            result['diff'] = {'prepared': diff_stdout}

    finally:
        # Always clean up the temp file
        module.run_command(['rm', '-f', remote_path])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
