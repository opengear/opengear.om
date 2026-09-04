# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


_COMMON_DISCOVER_OPTIONS = {
    "ports": {"type": "list", "elements": "int"},
    "username": {"type": "str"},
    "password": {"type": "str", "no_log": True},
    "apply_config": {"type": "bool"},
    "auth_timeout": {"type": "int"},
    "hostname_pattern": {"type": "str"},
}


class PortsAutoDiscoverArgs(object):
    argument_spec = {
        "config": {
            "type": "dict",
            "options": {
                "schedule": {
                    "type": "dict",
                    "options": dict(
                        _COMMON_DISCOVER_OPTIONS,
                        enabled={"type": "bool"},
                        period={
                            "type": "str",
                            "choices": ["daily", "weekly", "monthly"],
                        },
                        day_of_month={"type": "int"},
                        day_of_week={"type": "int"},
                        hour={"type": "int"},
                        minute={"type": "int"},
                    ),
                }
            },
        },
        "trigger": {
            "type": "dict",
            "options": _COMMON_DISCOVER_OPTIONS,
        },
        "cancel": {"type": "bool", "default": False},
        "state": {
            "type": "str",
            "default": "merged",
            "choices": ["merged", "replaced", "gathered", "rendered"],
        },
    }
