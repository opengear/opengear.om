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
module: ports_status
version_added: '1.0.0'
short_description: Gathers live status data for serial ports
description:
  - Returns read-only status information for serial ports including the
    current operating status, serial pin signal states, tx/rx byte counters,
    and PDU outlet associations.
  - This module is gather-only and never modifies device state.
  - Use M(opengear.ng.ports_config) to manage writable port configuration.
  - Use M(opengear.ng.ports_sessions) to inspect active sessions.
  - See also M(opengear.ng.ports_control) and M(opengear.ng.ports_auto_discover).
author:
  - Opengear (@opengear)
options:
  state:
    description: Must be C(gathered). This module only reads device state.
    type: str
    choices: [gathered]
    default: gathered
"""

EXAMPLES = """
- name: Gather port status
  opengear.ng.ports_status:
    state: gathered
  register: ports_status

- name: Assert all ports are in ok status
  ansible.builtin.assert:
    that:
      - item.status == 'ok'
    fail_msg: "Port {{ item.portnum }} status is {{ item.status }}"
  loop: "{{ ports_status.gathered }}"

- name: Show serial pin signal states and byte counters
  ansible.builtin.debug:
    msg: >
      Port {{ item.portnum }}: dcd={{ item.dcd }}, dsr={{ item.dsr }},
      tx={{ item.tx }} bytes, rx={{ item.rx }} bytes
  loop: "{{ ports_status.gathered }}"
"""

RETURN = """
gathered:
  description: Live status information for each serial port.
  returned: always
  type: list
  elements: dict
  contains:
    id:
      description: The API ID of the port.
      type: str
      returned: always
    name:
      description: The system-assigned port name.
      type: str
      returned: always
    portnum:
      description: The physical port number.
      type: int
      returned: always
    label:
      description: The configured port label.
      type: str
      returned: when configured
    mode:
      description: The current operating mode.
      type: str
      returned: always
    device:
      description: The device path for the port.
      type: str
      returned: always
    status:
      description: The hardware status of the port.
      type: str
      returned: always
    rts:
      description: State of the RTS (Request To Send) signal.
      type: bool
      returned: when available
    cts:
      description: State of the CTS (Clear To Send) signal.
      type: bool
      returned: when available
    dtr:
      description: State of the DTR (Data Terminal Ready) signal.
      type: bool
      returned: when available
    dsr:
      description: State of the DSR (Data Set Ready) signal.
      type: bool
      returned: when available
    dcd:
      description: State of the DCD (Data Carrier Detect) signal.
      type: bool
      returned: when available
    tx:
      description: Number of bytes transmitted on this port.
      type: int
      returned: when available
    rx:
      description: Number of bytes received on this port.
      type: int
      returned: when available
    pdu_outlets:
      description: PDU outlet IDs associated with this port.
      type: list
      returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.ports_status import PortsStatusArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.ports_status import PortsStatus


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    module = AnsibleModule(
        argument_spec=PortsStatusArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PortsStatus(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
