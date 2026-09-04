#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'opengear'
}

DOCUMENTATION = """
---
module: ports_control
version_added: '1.0.0'
short_description: Sends control actions to serial ports on Opengear devices
description:
  - Sends power (on, off, cycle) and tx/rx counter reset commands to one or
    more serial ports.
  - This is an action module — it is always reported as changed when commands
    are issued. Use check mode to preview commands without sending them.
  - Ports must have a PDU outlet association configured for power commands
    to take effect on the connected device.
notes:
  - None of these commands are idempotent. Each run sends the command to the
    device regardless of current state.
author:
  - Opengear (@opengear)
options:
  config:
    description: List of ports and the control command to issue to each.
    type: list
    elements: dict
    required: true
    suboptions:
      id:
        description: The ID of the port (e.g. C(ports-1)).
        type: str
      portnum:
        description: The physical port number.
        type: int
      name:
        description: The system-assigned port name (e.g. C(port01)).
        type: str
      command:
        description: The control command to issue.
        type: str
        required: true
        choices: ['on', 'off', cycle, reset_counters]
"""

EXAMPLES = """
- name: Power cycle a single port
  opengear.ng.ports_control:
    config:
      - portnum: 1
        command: cycle

- name: Power off multiple ports
  opengear.ng.ports_control:
    config:
      - portnum: 3
        command: 'off'
      - portnum: 4
        command: 'off'

- name: Reset tx/rx counters on a port
  opengear.ng.ports_control:
    config:
      - portnum: 1
        command: reset_counters

- name: Preview control commands without sending (check mode)
  opengear.ng.ports_control:
    config:
      - portnum: 1
        command: cycle
  check_mode: true
"""

RETURN = """
commands:
  description: The set of API commands that were (or would be) sent.
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.ports_control import PortsControlArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.ports_control import PortsControl


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    module = AnsibleModule(
        argument_spec=PortsControlArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PortsControl(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
