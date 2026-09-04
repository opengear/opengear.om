# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class PortsControlArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the ports_control module.
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "config": {
            "type": "list",
            "elements": "dict",
            "required": True,
            "options": {
                "id": {"type": "str"},
                "name": {"type": "str"},
                "portnum": {"type": "int"},
                "command": {
                    "type": "str",
                    "required": True,
                    "choices": ["on", "off", "cycle", "reset_counters"],
                },
            },
        },
    }
