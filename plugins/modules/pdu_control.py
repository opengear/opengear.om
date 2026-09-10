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
module: pdu_control
version_added: '1.0.0'
short_description: Sends power actions to PDU outlets on Opengear devices
description:
  - Sends on, off, and cycle power commands to one or more outlets on a PDU.
  - This is an action module, it is always reported as changed when
    commands are issued. Use check mode to preview commands without sending
    them.
author:
  - Opengear (@opengear)
options:
  config:
    description: List of PDUs and the outlets/action to issue to each.
    type: list
    elements: dict
    required: true
    suboptions:
      id:
        description: The unique id of the PDU.
        type: str
      name:
        description: A unique user specified name for the PDU.
        type: str
      outlets:
        description: The list of PDU outlet numbers to control.
        type: list
        elements: int
        required: true
      action:
        description: The power action to take on PDU outlets.
        type: str
        required: true
        choices: ['on', 'off', cycle]
"""

EXAMPLES = """
- name: Power on outlet 1 on a PDU identified by name
  opengear.ng.pdu_control:
    config:
      - name: rack-pdu-01
        outlets: [1]
        action: 'on'

- name: Power cycle multiple outlets on a PDU identified by id
  opengear.ng.pdu_control:
    config:
      - id: pdus-1
        outlets: [1, 4, 8]
        action: cycle

- name: Power off outlets across multiple PDUs
  opengear.ng.pdu_control:
    config:
      - name: rack-pdu-01
        outlets: [2]
        action: 'off'
      - name: rack-pdu-02
        outlets: [3]
        action: 'off'

- name: Preview control commands without sending (check mode)
  opengear.ng.pdu_control:
    config:
      - name: rack-pdu-01
        outlets: [1]
        action: cycle
  check_mode: true
"""

RETURN = """
commands:
  description: The set of API commands that were (or would be) sent.
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.pdu_control import PduControlArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.pdu_control import PduControl


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    module = AnsibleModule(
        argument_spec=PduControlArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PduControl(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
