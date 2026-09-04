#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "opengear",
}

DOCUMENTATION = """
---
module: facts
version_added: '1.0.0'
short_description: Gathers facts from Opengear devices
description:
  - Gathers facts from Opengear devices, including device information and configuration state for specified network resources.
author:
  - Opengear (@opengear)
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected to a given subset.
    required: false
    type: list
    elements: str
    default: 'all'
    version_added: '1.0.0'
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected to a given subset.
      - Use C(all) to gather all subsets except opt-in facts that must be requested explicitly
      - "Opt-in facts are: C(system_firmware_upgrade, user_authorized_keys, system_authorized_keys, ports_status)"
    required: false
    type: list
    elements: str
    choices:
      - all
      - auth
      - conns
      - failover
      - groups
      - physifs
      - ports_config
      - ports_status
      - pdu
      - services
      - static_routes
      - system_authorized_keys
      - system_config
      - system_diskspace
      - system_firmware_upgrade
      - system_info
      - system_time
      - user_authorized_keys
      - users
    version_added: '1.0.0'
"""

EXAMPLES = """
- name: Gather all facts (excludes opt-in subsets)
  opengear.ng.facts:
    gather_network_resources:
      - all

- name: Gather system configuration facts
  opengear.ng.facts:
    gather_network_resources:
      - system_config
      - system_time

- name: Gather system info and disk space facts
  opengear.ng.facts:
    gather_network_resources:
      - system_info
      - system_diskspace

- name: Gather system authorized keys (opt-in)
  opengear.ng.facts:
    gather_network_resources:
      - system_authorized_keys
"""

RETURN = """
ansible_network_resources:
  description: Facts gathered from the device.
  returned: always
  type: dict
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.facts import FactsArgs
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts


def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    module = AnsibleModule(argument_spec=FactsArgs.argument_spec,
                           supports_check_mode=True)
    warnings = []

    gather_network_resources = module.params.get('gather_network_resources')
    gather_subset = module.params.get('gather_subset')
    result = Facts(module).get_facts(
        legacy_facts_type=gather_subset,
        resource_facts_type=gather_network_resources
    )

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    for warning in warnings:
        module.warn(warning)
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
