# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts
from ansible_collections.opengear.ng.plugins.module_utils.utils.utils import (
    dict_diff,
    remove_empties,
)

_TRIGGER_PATH = "ports/auto_discover"
_SCHEDULE_PATH = "ports/auto_discover/schedule"

_TRIGGER_FIELDS = frozenset(
    {
        "ports",
        "username",
        "password",
        "apply_config",
        "auth_timeout",
        "hostname_pattern",
    }
)


class PortsAutoDiscover(ConfigBase):
    """
    Manages Port Auto-Discovery on Opengear devices.

    Handles schedule configuration (idempotent), discovery triggers, and
    cancellation of running discovery jobs.
    """

    gather_subset = ["!all", "!min"]
    gather_network_resources = ["ports_auto_discover"]

    def __init__(self, module):
        super(PortsAutoDiscover, self).__init__(module)

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        state = self._module.params["state"]
        result = {"changed": False}

        if state == "gathered":
            facts, _warnings = Facts(self._module).get_facts(
                self.gather_subset, self.gather_network_resources
            )
            result["gathered"] = facts["ansible_network_resources"].get(
                "ports_auto_discover", {}
            )
            return result

        if state == "rendered":
            config = self._module.params.get("config") or {}
            schedule = remove_empties(config.get("schedule") or {})
            result["rendered"] = {"auto_discover_schedule": schedule}
            return result

        commands = []
        diff = {}

        # Schedule config (merged/replaced)
        config = self._module.params.get("config") or {}
        schedule_want = config.get("schedule")
        if schedule_want is not None:
            want_clean = remove_empties(schedule_want)
            have = self._get_schedule()
            if state == "merged":
                target = deepcopy(have)
                target.update(want_clean)
            else:
                target = want_clean
            if dict_diff(target, have):
                commands.append(
                    {
                        "method": "PUT",
                        "path": _SCHEDULE_PATH,
                        "data": {"auto_discover_schedule": target},
                    }
                )
                if self._module._diff:
                    diff = {"before": have, "after": target}

        # Trigger discovery
        trigger = self._module.params.get("trigger")
        if trigger is not None:
            body = {
                k: v
                for k, v in trigger.items()
                if k in _TRIGGER_FIELDS and v is not None
            }
            body["ports"] = trigger.get("ports")
            commands.append(
                {
                    "method": "POST",
                    "path": _TRIGGER_PATH,
                    "data": {"auto_discover": body},
                }
            )

        # Cancel running discovery
        if self._module.params.get("cancel"):
            if self._is_running():
                commands.append(
                    {"method": "DELETE", "path": _TRIGGER_PATH, "data": None}
                )

        if commands:
            if not self._module.check_mode:
                for cmd in commands:
                    try:
                        self._connection.send_request(
                            cmd["data"], cmd["path"], cmd["method"]
                        )
                    except ConnectionError as exc:
                        if not exc.args[0].startswith("Expecting value:"):
                            raise
            result["changed"] = True

        result["commands"] = commands
        if diff:
            result["diff"] = diff
        return result

    def _get_schedule(self):
        try:
            resp = self._connection.send_request(None, _SCHEDULE_PATH)
            return resp.get("auto_discover_schedule") or {}
        except Exception:
            return {}

    def _is_running(self):
        try:
            resp = self._connection.send_request(None, _TRIGGER_PATH)
            return resp.get("auto_discover", {}).get("status") == "running"
        except Exception:
            return False
