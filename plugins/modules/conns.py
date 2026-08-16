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
module: conns
version_added: '1.0.0'
short_description: Manages network connection configuration for Opengear devices
description:
  - Manages network connection configuration for Opengear devices
author:
  - Opengear (@opengear)
options:
  config:
    description: Manage network connection configuration for Opengear devices
    type: list
    elements: dict
    suboptions:
      id:
        type: str
        description: id
      name:
        type: str
        description: name
      mode:
        type: str
        description: mode
      physif:
        type: str
        description: physical interface of conn
      ipv4_static_settings:
        type: dict
        description: ipv4 static setting
        suboptions:
          netmask:
            type: str
            description: subnet mask
          address:
            type: str
            description: ip address
          broadcast:
            type: str
            description: broadcast address
          gateway:
            type: str
            description: gateway address
          dns1:
            type: str
            description: primary dns server
          dns2:
            type: str
            description: secondary dns server
      ipv6_static_settings:
        type: dict
        description: ipv6 static settings
        suboptions:
          prefix_length:
            type: str
            description: prefix length
          address:
            type: str
            description: ipv6 address
          gateway:
            type: str
            description: ipv6 gateway address
          dns1:
            type: str
            description: primary dns server
          dns2:
            type: str
            description: secondary dns server
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

RETURN = """
before:
  description: The configuration before the module is executed.
  returned: always
  type: dict
after:
  description: The configuration after the module is executed.
  returned: when changed
  type: dict
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.conns import ConnsArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.conns import Conns


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=ConnsArgs.argument_spec,
                           supports_check_mode=True)

    result = Conns(module).execute_module()
    for warning in result.pop('warnings', []):
        module.warn(warning)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
