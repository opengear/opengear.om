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
module: pdu_status
version_added: '1.0.0'
short_description: Gathers live status for PDUs and their outlets
description:
  - Returns read-only status information for PDUs connected to Opengear
    devices, including outlet count and per-outlet status, and last action
    details.
  - This module is gather-only and never modifies device state.
  - Use M(opengear.ng.pdu_config) to manage writable PDU configuration.
  - See also M(opengear.ng.pdu_control) for outlet power actions.
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
- name: Gather PDU status
  opengear.ng.pdu_status:
    state: gathered
  register: pdu_status

- name: Show outlets that are currently off
  ansible.builtin.debug:
    msg: "{{ pdu.name }} outlet {{ outlet.number }} ({{ outlet.name }}) is off"
  loop: "{{ pdu_status.gathered | subelements('outlets') }}"
  loop_control:
    loop_var: item
  vars:
    pdu: "{{ item[0] }}"
    outlet: "{{ item[1] }}"
  when: item[1].status == 'off'
"""

RETURN = """
gathered:
  description: Live status information for each PDU.
  returned: always
  type: list
  elements: dict
  contains:
    id:
      description: The unique id of the PDU.
      type: str
      returned: always
    name:
      description: A unique user specified name for the PDU.
      type: str
      returned: always
    driver:
      description: The driver to use to control and monitor the PDU.
      type: dict
      returned: always
    method:
      description: The method to used to access the PDU, can be 'snmp', 'powerman' or 'shell'.
      type: str
      returned: always
    monitor:
      description: If true the pdu outlets are monitored for any change in status.
      type: bool
      returned: always
    outlet_count:
      description: The number of outlets on the PDU.
      type: int
      returned: when available
    outlets:
      description: The list of power outlets controlled by this PDU.
      type: list
      returned: always
      elements: dict
      contains:
        id:
          description: The unique identifier for the PDU outlet.
          type: str
        number:
          description: The outlet number of this PDU. (read only)
          type: int
        name:
          description: The name associated with this PDU outlet.
          type: str
        port:
          description: The serial port ID that is associated with this PDU outlet.
          type: str
        status:
          description: The current power status of the outlet.
          type: str
        status_timestamp:
          description: When the status was last observed.
          type: str
        last_action:
          description: The last power action sent to the outlet.
          type: str
        last_action_timestamp:
          description: When the last action was issued.
          type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.pdu_status import PduStatusArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.pdu_status import PduStatus


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    module = AnsibleModule(
        argument_spec=PduStatusArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PduStatus(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
