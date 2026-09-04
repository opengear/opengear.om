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
module: ports_auto_discover
version_added: '1.0.0'
short_description: Manages Port Auto-Discovery on Opengear devices
description:
  - Configures the scheduled Port Auto-Discovery process and can trigger or
    cancel discovery runs on demand.
  - Schedule configuration is idempotent — the schedule is only updated when
    the desired state differs from the current configuration on the device.
  - Triggering a discovery (C(trigger)) is always reported as changed.
  - Cancelling a discovery (C(cancel)) is idempotent — no change is reported
    if no discovery is currently running.
  - Use M(opengear.ng.ports_status) to check the current status and active
    sessions of individual ports after a discovery run.
notes:
  - I(password) fields are marked C(no_log) and will not appear in module output.
author:
  - Opengear (@opengear)
options:
  config:
    description:
      - Schedule configuration for the periodic Port Auto-Discovery process.
      - Applied when I(state) is C(merged), C(replaced), or C(rendered).
    type: dict
    suboptions:
      schedule:
        description: The auto-discovery schedule settings.
        type: dict
        suboptions:
          enabled:
            description: Whether periodic auto-discovery is active.
            type: bool
          period:
            description: Frequency of scheduled discovery runs.
            type: str
            choices: [daily, weekly, monthly]
          day_of_month:
            description: Day of month (1-31) for C(monthly) schedules.
            type: int
          day_of_week:
            description: Day of week (0=Sunday to 6=Saturday) for C(weekly) schedules.
            type: int
          hour:
            description: Hour of day (0-23) to run discovery.
            type: int
          minute:
            description: Minute of hour (0-59) to run discovery.
            type: int
          ports:
            description: List of port numbers to include in scheduled discovery.
            type: list
            elements: int
          username:
            description: Username for port login attempts during discovery.
            type: str
          password:
            description: Password for port login attempts during discovery.
            type: str
          apply_config:
            description: Whether to apply discovered settings to port configuration.
            type: bool
          auth_timeout:
            description: Authentication timeout in seconds (0 uses the default).
            type: int
          hostname_pattern:
            description: Regex pattern to match on hostname labels (empty uses default).
            type: str
  trigger:
    description:
      - Triggers an immediate Port Auto-Discovery run.
      - Omit I(ports) or set it to an empty list to discover all ports.
      - Always reported as changed. Use check mode to preview without running.
    type: dict
    suboptions:
      ports:
        description: >
          List of port numbers to discover. Omit or set to C(null) to
          discover all available ports.
        type: list
        elements: int
      username:
        description: Username for port login attempts during discovery.
        type: str
      password:
        description: Password for port login attempts during discovery.
        type: str
      apply_config:
        description: Whether to apply discovered settings to port configuration.
        type: bool
      auth_timeout:
        description: Authentication timeout in seconds (0 uses the default).
        type: int
      hostname_pattern:
        description: Regex pattern to match on hostname labels (empty uses default).
        type: str
  cancel:
    description:
      - When C(true), cancels any running Port Auto-Discovery job.
      - Idempotent — no change is reported if no discovery is running.
    type: bool
    default: false
  state:
    description:
      - C(merged) — update the schedule with the provided I(config), preserving
        fields not specified in the play.
      - C(replaced) — replace the schedule with exactly the provided I(config).
      - C(gathered) — return the current schedule and discovery status without
        making any changes.
      - C(rendered) — return what would be sent to the API without connecting
        to a device.
      - I(trigger) and I(cancel) are executed regardless of I(state).
    type: str
    default: merged
    choices: [merged, replaced, gathered, rendered]
"""

EXAMPLES = """
- name: Configure a daily auto-discovery schedule
  opengear.ng.ports_auto_discover:
    config:
      schedule:
        enabled: true
        period: daily
        hour: 2
        minute: 30
        ports:
          - 1
          - 2
          - 3

- name: Disable scheduled auto-discovery
  opengear.ng.ports_auto_discover:
    config:
      schedule:
        enabled: false

- name: Trigger discovery on all ports immediately
  opengear.ng.ports_auto_discover:
    trigger: {}

- name: Trigger discovery on specific ports with credentials
  opengear.ng.ports_auto_discover:
    trigger:
      ports:
        - 1
        - 5
        - 10
      username: admin
      password: secret
      apply_config: true

- name: Configure schedule and trigger immediately
  opengear.ng.ports_auto_discover:
    config:
      schedule:
        enabled: true
        period: weekly
        day_of_week: 0
        hour: 3
        minute: 0
    trigger:
      ports:
        - 1

- name: Cancel a running auto-discovery job
  opengear.ng.ports_auto_discover:
    cancel: true

- name: Gather current auto-discovery status and schedule
  opengear.ng.ports_auto_discover:
    state: gathered
  register: ad_facts

- name: Show discovery status
  ansible.builtin.debug:
    var: ad_facts.gathered.status

- name: Preview schedule config without connecting
  opengear.ng.ports_auto_discover:
    config:
      schedule:
        enabled: true
        period: daily
        hour: 4
    state: rendered
"""

RETURN = """
commands:
  description: The set of API commands that were (or would be) sent.
  returned: when state is not gathered or rendered
  type: list
gathered:
  description: Current auto-discovery status and schedule from the device.
  returned: when state is gathered
  type: dict
  contains:
    status:
      description: Current discovery process status.
      type: dict
    schedule:
      description: Current scheduled discovery configuration.
      type: dict
rendered:
  description: The API request body that would be sent for the schedule config.
  returned: when state is rendered
  type: dict
diff:
  description: Before/after comparison of schedule changes.
  returned: when a schedule change is made and diff mode is enabled
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.opengear.ng.plugins.module_utils.argspec.ports_auto_discover import PortsAutoDiscoverArgs
from ansible_collections.opengear.ng.plugins.module_utils.config.ports_auto_discover import PortsAutoDiscover


def main():
    """
    Main entry point for module execution.

    :returns: the result from module invocation
    """
    module = AnsibleModule(
        argument_spec=PortsAutoDiscoverArgs.argument_spec,
        supports_check_mode=True,
    )

    result = PortsAutoDiscover(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
