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
module: config_import
version_added: '1.0.0'
short_description: Import configuration on Opengear devices
description:
  - Merges a provided configuration into the current device configuration
    using the C(config import) command.
  - The provided configuration content is written to a temporary file on the
    device, imported using C(config import), and removed after import.
  - Use the C(config_diff) module to preview changes before importing.
author:
  - Opengear (@opengear)
options:
  config_content:
    description:
      - The configuration content in dotnotation format to import into the
        device configuration. Use the C(lookup) plugin or C(config_export)
        module to obtain this content.
    type: str
    required: true
  remote_tmp_dir:
    description:
      - Temporary directory on the device to store the config file during import.
    type: str
    default: /tmp
notes:
  - This module requires C(ansible_connection) set to C(ssh) for the task
    or host. It cannot use the httpapi connection plugin.
  - The user must have admin access on the device.
  - The configuration file must have been exported from a device running
    the same firmware version and SKU. These values are checked at the
    top of the export file.
  - C(config import) merges configuration into the current device
    configuration. If an error occurs, the device will automatically
    roll back to the previous configuration. The error details are
    returned in the module failure message.
  - Use C(config_restore) for full configuration replacement instead of merge.
  - Use C(config_diff) to preview changes before importing.
"""

EXAMPLES = """
- name: Import configuration
  opengear.ng.config_import:
    config_content: "{{ lookup('file', config_backup_file) }}"
  vars:
    ansible_connection: ssh
  register: import_result

- name: Show import result
  ansible.builtin.debug:
    var: import_result.msg
"""

RETURN = """
changed:
  description: True if the configuration was imported successfully.
  returned: always
  type: bool
msg:
  description: Output from the config import command.
  returned: always
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
    remote_path = os.path.join(remote_tmp_dir, f"ansible_config_import_{os.getpid()}.cfg")

    result = {'changed': False}

    if module.check_mode:
        result['changed'] = True
        module.exit_json(**result)

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

        # Run config import on the device
        import_rc, import_stdout, import_stderr = module.run_command(
            ['config', 'import', remote_path]
        )

        if import_rc != 0:
            module.fail_json(
                msg=import_stderr.strip(),
                rc=import_rc,
            )

        result['changed'] = True
        result['msg'] = import_stdout.strip()

    finally:
        # Always clean up the temp file
        module.run_command(['rm', '-f', remote_path])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
