#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
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
module: pdu_config
version_added: '1.0.0'
short_description: Manages configuration for PDUs connected to Opengear devices
description:
  - Manages writable configuration for PDUs connected to Opengear devices,
    including access method, connection settings, and outlet name/port
    mapping.
  - Read-only fields (outlet status, outlet_count, last_action) are returned
    by the M(opengear.ng.pdu_status) module.
  - Outlet power control is handled by M(opengear.ng.pdu_control).
author:
  - Opengear (@opengear)
options:
  config:
    description: Manage configuration for PDUs connected to Opengear devices
    type: list
    elements: dict
    suboptions:
      id:
        description: The unique id of the PDU.
        type: str
      name:
        description: A unique user specified name for the PDU.
        type: str
      driver:
        description: The driver to use to control and monitor the PDU.
        type: dict
        suboptions:
          id:
            description: The identifier of the PDU driver to use.
            type: str
          name:
            description: The name of the PDU driver.
            type: str
      method:
        description: The method to used to access the PDU, can be 'snmp', 'powerman' or 'shell'.
        type: str
        choices: [powerman, shell, snmp]
      monitor:
        description: If true the pdu outlets are monitored for any change in status.
        type: bool
      powerman:
        description: >
          The configuration for the powerman PDU method. Applies only when
          C(method=powerman).
        type: dict
        suboptions:
          id:
            description: The unique identifier of this serial PDU configuration.
            type: str
          username:
            description: >
              The user account on the PDU that will be used for access over
              serial connection.
            type: str
          password:
            description: The password to be used to access this PDU over serial connection.
            type: str
          port:
            description: The port ID that is associated with this PDU.
            type: str
      shell:
        description: >
          The configuration for the shell PDU method. Applies only when
          C(method=shell).
        type: dict
        suboptions:
          id:
            description: The unique identifier of this serial PDU configuration.
            type: str
          username:
            description: >
              The user account on the PDU that will be used for access over
              serial connection.
            type: str
          password:
            description: The password to be used to access this PDU over serial connection.
            type: str
          port:
            description: The port ID that is associated with this PDU.
            type: str
      snmp:
        description: >
          The configuration for the SNMP PDU method. Applies only when
          C(method=snmp).
        type: dict
        suboptions:
          id:
            description: The unique identifier for this SNMP PDU.
            type: str
          protocol:
            description: >
              The protocol that is used to access this PDU via SNMP. The
              default protocol is UDP.
            type: str
            choices: [UDP, TCP]
          address:
            description: The network address of this PDU to be accessed via SNMP.
            type: str
          port:
            description: The port to be used to access this PDU via SNMP.
            type: int
          version:
            description: The version of SNMP used to access this PDU.
            type: str
            choices: ['1', '2c', '3']
          community:
            description: >
              The community string used to access this PDU via SNMP.
              Applies when C(version) is C(1) or C(2c).
            type: str
          auth_protocol:
            description: >
              The authentication protocol used to access this PDU via SNMPv3.
            type: str
            choices: [SHA, MD5, SHA-512, SHA-384, SHA-256, SHA-224]
          auth_password:
            description: The authentication password to access this PDU via SNMPv3.
            type: str
          security_name:
            description: >
              The security name used to access this PDU via SNMPv3.
              Required when C(version=3).
            type: str
          engine_id:
            description: The unique identifier string of the SNMP agent of this PDU.
            type: str
          privacy_protocol:
            description: The privacy protocol used to access this PDU via SNMPv3.
            type: str
            choices: [DES, AES, AES-192, AES-256]
          privacy_password:
            description: The privacy password used to access this PDU via SNMPv3.
            type: str
          security_level:
            description: The security level to access this PDU via SNMPv3.
            type: str
            choices: [noAuthNoPriv, authNoPriv, authPriv]
      outlets:
        description: >
          The list of power outlets controlled by this PDU. Outlet power
          status is surfaced by M(opengear.ng.pdu_status).
        type: list
        elements: dict
        suboptions:
          number:
            description: The outlet number of this PDU. (read only)
            type: int
          name:
            description: The name associated with this PDU outlet.
            type: str
          port:
            description: The serial port ID that is associated with this PDU outlet.
            type: str
  state:
    description:
    - The state of the configuration after module completion.
    type: str
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    - gathered
    - rendered
    default: merged
"""

EXAMPLES = """
- name: Configure a PDU via SNMP
  opengear.ng.pdu_config:
    config:
      - name: rack-pdu-01
        driver:
          id: apc24
        method: snmp
        monitor: true
        snmp:
          address: 192.168.1.50
          version: '2c'
          community: public
          port: 161
    state: merged

- name: Configure a PDU via shell
  opengear.ng.pdu_config:
    config:
      - name: rack-pdu-02
        driver:
          id: apc_pdu
        method: shell
        shell:
          username: admin
          password: "{{ vault_pdu_password }}"
          port: ports-3
    state: merged

- name: Name and map outlets on an existing PDU
  opengear.ng.pdu_config:
    config:
      - name: rack-pdu-01
        outlets:
          - number: 1
            name: web-server-1
          - number: 2
            name: web-server-2
    state: merged

- name: Remove a PDU
  opengear.ng.pdu_config:
    config:
      - name: rack-pdu-02
    state: deleted

- name: Gather existing PDU configuration
  opengear.ng.pdu_config:
    state: gathered
"""

RETURN = """
before:
  description: The configuration before the module is executed.
  returned: always
  type: list
after:
  description: The configuration after the module is executed.
  returned: when changed
  type: list
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.pdu_config import PduConfigArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.pdu_config import PduConfig


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(
        argument_spec=PduConfigArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PduConfig(module).execute_module()
    for warning in result.pop('warnings', []):
        module.warn(warning)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
