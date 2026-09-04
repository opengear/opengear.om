# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy
import json

from ansible.module_utils.connection import ConnectionError

from ansible_collections.opengear.ng.plugins.module_utils.config.base import ConfigBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.facts import Facts
from ansible_collections.opengear.ng.plugins.module_utils.utils.utils import (
    command_builder,
    dict_diff,
    remove_empties,
    to_list,
)

# Identification-only fields that must not appear in PUT request bodies
_BODY_EXCLUDE = frozenset({"id", "name", "portnum"})


def _ip_alias_equal(a, b):
    """Compare two ip_alias lists order-insensitively."""
    if len(a) != len(b):
        return False

    def key(x):
        return json.dumps(x, sort_keys=True)
    return sorted(a, key=key) == sorted(b, key=key)


def _port_diff(want, have):
    """Compare two port dicts, handling ip_alias (list-of-dicts) separately
    to avoid the TypeError that sorted() raises on unhashable dict items."""
    a = deepcopy(want)
    b = deepcopy(have)
    a_alias = a.pop("ip_alias", None)
    b_alias = b.pop("ip_alias", None)

    diff = dict_diff(a, b)

    if a_alias is not None or b_alias is not None:
        if not _ip_alias_equal(a_alias or [], b_alias or []):
            diff["ip_alias"] = a_alias

    return diff


def _merge_port(device, want):
    """Merge want into device. control_code is merged key-by-key so that
    specifying a single escape code does not wipe unmentioned codes."""
    result = deepcopy(device)
    for key, value in want.items():
        if (
            key == "control_code"
            and isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = {**result[key], **value}
        else:
            result[key] = value
    return result


def _find_port_id(portnum_id_map, name_id_map, port):
    """Resolve port identity from id, portnum, or name.  Pops consumed keys."""
    port_id = port.pop("id", None)
    if port_id:
        return port_id
    portnum = port.pop("portnum", None)
    if portnum is not None and portnum in portnum_id_map:
        return portnum_id_map[portnum]
    name = port.get("name")
    if name and name in name_id_map:
        return name_id_map[name]
    return None


class PortsConfig(ConfigBase):
    """
    Manages configuration of serial ports on Opengear devices.
    """

    gather_subset = ["!all", "!min"]
    gather_network_resources = ["ports_config"]

    def __init__(self, module):
        super(PortsConfig, self).__init__(module)
        self.current_state = {}

    def get_ports_facts(self, data=None):
        """Get the 'facts' (the current configuration).

        :rtype: A list
        :returns: The current configuration as a list of port dicts
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data
        )
        ports_facts = facts["ansible_network_resources"].get("ports_config")
        if not ports_facts:
            return []
        return ports_facts

    def execute_module(self):
        """Execute the module.

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {"changed": False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_ports_facts = self.get_ports_facts()
        else:
            existing_ports_facts = {}

        if self.state in self.ACTION_STATES or self.state == "rendered":
            commands.extend(self.set_config(existing_ports_facts, warnings))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    port_id = command["path"].split("/")[-1]
                    try:
                        response = self._connection.send_request(
                            command["data"], command["path"], command["method"]
                        )
                        if command["method"] == "PUT":
                            self.current_state[port_id] = response.get("port", {})
                    except ConnectionError as exc:
                        if not exc.args[0].startswith("Expecting value:"):
                            raise exc
            else:
                # Simulate state changes for check mode + diff
                for command in commands:
                    if command["method"] == "PUT":
                        port_id = command["path"].split("/")[-1]
                        if port_id in self.current_state:
                            self.current_state[port_id].update(command["data"]["port"])
            result["changed"] = True

        result["commands"] = commands

        if self.state in self.ACTION_STATES or self.state == "gathered":
            changed_ports_facts = self.get_ports_facts(self.current_state.values())
        elif self.state == "rendered":
            result["rendered"] = commands

        if self.state in self.ACTION_STATES:
            result["before"] = existing_ports_facts
            if result["changed"]:
                result["after"] = changed_ports_facts
                if self._module._diff:
                    diff_before = []
                    diff_after = []
                    existing_by_id = {
                        p["id"]: p for p in existing_ports_facts if p.get("id")
                    }
                    for command in commands:
                        if command["method"] == "PUT":
                            port_id = command["path"].split("/")[-1]
                            if port_id in existing_by_id:
                                before = existing_by_id[port_id]
                                after = {**before, **command["data"]["port"]}
                                diff_before.append(before)
                                diff_after.append(after)
                    result["diff"] = {
                        "before": json.dumps(diff_before, indent=4) + "\n",
                        "after": json.dumps(diff_after, indent=4) + "\n",
                    }
        elif self.state == "gathered":
            result["gathered"] = changed_ports_facts

        result["warnings"] = warnings
        return result

    def set_config(self, existing_ports_facts, warnings):
        """Collect args and current config, return required commands.

        :rtype: A list
        :returns: commands necessary to reach the desired configuration
        """
        want = self._module.params["config"]
        have = existing_ports_facts
        resp = self.set_state(want, have, warnings)
        return to_list(resp)

    def set_state(self, want, have, warnings):
        """Select the appropriate state handler.

        :param want: desired configuration (list of port dicts)
        :param have: current configuration (list of port dicts)
        :rtype: A list
        :returns: commands necessary to reach the desired configuration
        """
        portnum_id_map = {}
        name_id_map = {}
        id_port_map = {}

        for port in have:
            pid = port.get("id")
            if pid:
                id_port_map[pid] = port
                pnum = port.get("portnum")
                if pnum is not None:
                    portnum_id_map[pnum] = pid
                pname = port.get("name")
                if pname:
                    name_id_map[pname] = pid

        self.current_state = deepcopy(id_port_map)

        state = self._module.params["state"]
        if state == "overridden":
            commands = self._state_overridden(
                want, portnum_id_map, name_id_map, id_port_map
            )
        elif state == "replaced":
            commands = self._state_replaced(
                want, portnum_id_map, name_id_map, id_port_map
            )
        elif state == "merged":
            commands = self._state_merged(
                want, portnum_id_map, name_id_map, id_port_map
            )
        else:
            commands = []
        return commands

    @staticmethod
    def _state_merged(want, portnum_id_map, name_id_map, id_port_map):
        """Merge the desired config into the current config.

        Existing port fields not mentioned in want are preserved.
        control_code values are merged key-by-key; all other list/scalar
        fields specified in want replace the corresponding device value.
        """
        commands = []
        for port in want:
            port = deepcopy(port)
            port_id = _find_port_id(portnum_id_map, name_id_map, port)
            data = remove_empties(port)

            if port_id in id_port_map:
                device_port = remove_empties(id_port_map[port_id])
                device_clean = {
                    k: v for k, v in device_port.items() if k not in _BODY_EXCLUDE
                }
                merged = _merge_port(
                    device_clean,
                    {k: v for k, v in data.items() if k not in _BODY_EXCLUDE},
                )
                if not _port_diff(merged, device_clean):
                    continue
                data = {k: merged[k] for k in merged}
            else:
                continue  # ports cannot be created

            body = {k: v for k, v in data.items() if k not in _BODY_EXCLUDE}
            command = command_builder({"port": body}, "ports/", port_id)
            if command:
                commands.append(command)
        return commands

    @staticmethod
    def _state_replaced(want, portnum_id_map, name_id_map, id_port_map):
        """Update named ports with the desired config.

        Identical to merged.
        """
        return PortsConfig._state_merged(want, portnum_id_map, name_id_map, id_port_map)

    @staticmethod
    def _state_overridden(want, portnum_id_map, name_id_map, id_port_map):
        """Apply replaced semantics across all specified ports.

        Ports not mentioned in want are left untouched (serial ports cannot
        be deleted via the API).
        """
        return PortsConfig._state_replaced(
            want, portnum_id_map, name_id_map, id_port_map
        )
