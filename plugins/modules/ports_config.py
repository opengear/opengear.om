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
module: ports_config
version_added: '1.0.0'
short_description: Manages configuration of serial ports on Opengear devices
description:
  - Manages writable configuration of serial ports on Opengear devices.
  - Read-only fields (status, sessions, pdu_outlets) are surfaced by the
    M(opengear.ng.ports_status) module.
  - Auto-discovery, power control, and session management are handled by
    dedicated modules.
notes:
  - Diff output shows the expected configuration change based on the commands
    generated. It does not reflect the actual device state after execution,
    which may differ due to device-side normalization or concurrent changes.
    Use state=gathered after a run to verify the actual device state.
author:
  - Opengear (@opengear)
options:
  config:
    description: Manage configuration of serial ports on Opengear devices
    type: list
    elements: dict
    suboptions:
      id:
        description: >
          The ID of the port (e.g. C(ports-1)). Used to identify the port
          when neither C(portnum) nor C(name) is provided.
        type: str
      portnum:
        description: >
          The physical port number on the device. (e.g. C(1)).
        type: int
      name:
        description: >
          The system-assigned port name (e.g. C(port01)). Read-only on the
          device; used here as an alternative identifier.
        type: str
      label:
        description: A human-readable label for the port.
        type: str
      mode:
        description: The operating mode of the port.
        type: str
        choices: [consoleServer, localConsole, disabled]
      baudrate:
        description: The communication rate of the port in bits per second.
        type: str
        choices: ['50', '75', '110', '134', '150', '200', '300', '600', '1200',
                  '1800', '2400', '4800', '9600', '19200', '38400', '57600',
                  '115200', '230400']
      databits:
        description: The number of data bits per character.
        type: str
        choices: ['7', '8']
      stopbits:
        description: The number of stop bits per character.
        type: str
        choices: ['1', '2']
      parity:
        description: The parity mode.
        type: str
        choices: [none, odd, even]
      pinout:
        description: The physical pinout of the port connector.
        type: str
        choices: [X1, X2, USB]
      logging_level:
        description: The level of data logging for the port.
        type: str
        choices: [disabled, eventsOnly, eventsAndReceivedCharacters, eventsAndAllCharacters]
      escape_char:
        description: >
          The pmshell escape character. Applies only when C(mode=consoleServer).
        type: str
      terminal_emulation:
        description: >
          The terminal emulation type. Applies only when C(mode=localConsole).
        type: str
        choices: [vt100, vt102, vt220, ansi, linux]
      kernel_debug:
        description: >
          Emit kernel debug messages from this port. Only one port per device
          may have this enabled. Applies only when C(mode=localConsole).
        type: bool
      single_session:
        description: Restrict the port to a single active session at a time.
        type: bool
      raw_tcp:
        description: Enable raw TCP access to the port.
        type: bool
      dtr_mode:
        description: Controls the DTR signal behaviour.
        type: str
        choices: [alwayson, activeuser, alwaysoff]
      ip_alias:
        description: >
          IP aliases for dedicated access to this port (consoleServer mode only).
        type: list
        elements: dict
        suboptions:
          ipaddress:
            description: The IP address of the alias.
            type: str
          interface:
            description: The network interface to bind the alias to.
            type: str
      control_code:
        description: >
          pmshell control-key sequences. In C(state=merged), only the keys
          provided are updated; unspecified keys retain their current value.
        type: dict
        suboptions:
          quit:
            description: Key sequence to quit pmshell.
            type: str
          chooser:
            description: Key sequence to open the port chooser.
            type: str
          power:
            description: Key sequence for the power menu.
            type: str
          portlog:
            description: Key sequence to display the port log.
            type: str
          pmhelp:
            description: Key sequence to display help.
            type: str
          break:
            description: Key sequence to send a break signal.
            type: str
  state:
    description:
      - The state of the configuration after module completion.
      - C(merged) updates only the fields specified, preserving all others.
      - C(replaced) behaves identically to C(merged) for this module.
      - C(overridden) is an alias for C(replaced) — serial ports cannot be
        deleted via the API
      - C(gathered) reads the current device configuration and returns it
        without making changes.
      - C(rendered) generates commands without contacting the device.
    type: str
    choices: [merged, replaced, overridden, gathered, rendered]
    default: merged
"""

EXAMPLES = """
- name: Set label and baud rate on port 1 (merged)
  opengear.ng.ports_config:
    config:
      - portnum: 1
        label: router-console
        baudrate: '9600'
    state: merged

- name: Configure a console server port (replaced)
  opengear.ng.ports_config:
    config:
      - portnum: 2
        label: switch-console
        mode: consoleServer
        baudrate: '115200'
        databits: '8'
        parity: none
        stopbits: '1'
        logging_level: eventsOnly
        single_session: true
        escape_char: '~'
    state: replaced

- name: Configure a local console port
  opengear.ng.ports_config:
    config:
      - portnum: 3
        mode: localConsole
        terminal_emulation: vt220
        kernel_debug: false
    state: merged

- name: Add an IP alias to a port
  opengear.ng.ports_config:
    config:
      - portnum: 4
        ip_alias:
          - ipaddress: 192.168.100.1
            interface: net1
    state: merged

- name: Configure a custom pmshell escape character
  opengear.ng.ports_config:
    config:
      - portnum: 1
        control_code:
          quit: '~.'
    state: merged

- name: Disable a port by ID
  opengear.ng.ports_config:
    config:
      - id: ports-5
        mode: disabled
    state: merged

- name: Gather port configuration facts
  opengear.ng.facts:
    gather_network_resources:
      - ports_config
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
  description: The set of API commands pushed to the remote device.
  returned: always
  type: list
diff:
  description: >
    A before/after JSON diff of the changed ports when diff mode is enabled.
    Only present when changes were made.
  returned: when changed and diff mode is active
  type: dict
rendered:
  description: The set of commands generated without contacting the device.
  returned: when state is rendered
  type: list
gathered:
  description: The configuration gathered from the device.
  returned: when state is gathered
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.ports_config import PortsConfigArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.ports_config import PortsConfig


def main():
    """
    Main entry point for module execution.

    :returns: the result form module invocation
    """
    module = AnsibleModule(
        argument_spec=PortsConfigArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PortsConfig(module).execute_module()
    for warning in result.pop('warnings', []):
        module.warn(warning)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
