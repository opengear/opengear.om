#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'opengear'
}

DOCUMENTATION = """
---
module: om_ports
version_added: 1.0.0
short_description: Manages port attributes of om ports
description:
  - Manages port attributes of om ports
author:
  - "Adrian Van Katwyk (@avankatwky)"
  - "Matt Witmer (@mattwit)"
options:
  config:
    description: Configuring and viewing ports information
    type: dict
    suboptions:
      ports:
        type: list
        elements: dict
        description: ports
        suboptions:
          id:
            description: The ID of the serial port. This ID can be used to fetch individual ports using the /ports/endpoint.
            type: str
          parity:
            description: The format of the parity byte.
            type: str
          label:
            description: The label for the serial port.
            type: str
          stopbits:
            description: The number of stop bits between characters.
            type: str
          pinout:
            description: The physical pinout of the port connector.
            type: str
          ip_alias:
            description: (consoleServer mode only) An IP address for dedicated access to a specific serial or USB console port.
            type: list
            elements: dict
            suboptions:
              ipaddress:
                description: ip address of port
                type: str
              interface:
                description: interface
                type: str
          baudrate:
            description: The communication rate of the port.
            type: str
          mode:
            description: The mode that the port is in.
            type: str
          logging_level:
            description: Indicates the logging level of the port.
            type: str
          databits:
            description: The number of data bits in a character.
            type: str
          escape_char:
            description: (consoleServer mode only) The escape character for pmshell.
            type: str
          terminal_emulation:
            description: (localConsole mode only) The terminal emulation type.
            type: str
          kernel_debug:
            description: (localConsole mode only) Emits kernel debug messages from the chosen port. Only one instance of this is allowed per device.
            type: bool
          sessions:
            description: sessions
            type: list
            elements: dict
            suboptions:
              username:
                description: username
                type: str
              client_pid:
                description: client pid
                type: int
          power:
            description: power level
            type: str
      auto_discover:
        description: auto disc
        type: dict
        suboptions:
          ports:
            type: list
            elements: int
            description: ports
          schedule:
            type: dict
            description: schedule
            suboptions:
              enabled:
                type: bool
                description: enabled or disabled
              period:
                type: str
                description: period
              day_of_month:
                type: int
                description: month
              day_of_week:
                type: int
                description: week
              hour:
                type: int
                description: hour
              minute:
                type: int
                description: minute
          start:
            description: Triggers the port Auto-Discovery process if start value is true.
            type: bool
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

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.om.plugins.module_utils.network.om.argspec.ports.ports import PortsArgs
from ansible_collections.opengear.om.plugins.module_utils.network.om.config.ports.ports import Ports


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=PortsArgs.argument_spec,
                           supports_check_mode=True)

    result = Ports(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
