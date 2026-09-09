# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class PortsSessionsArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the ports_sessions module.
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "config": {
            "type": "list",
            "elements": "dict",
            "options": {
                "id": {"type": "str"},
                "name": {"type": "str"},
                "portnum": {"type": "int"},
                "client_pid": {
                    "type": "list",
                    "elements": "int",
                },
            },
        },
        "state": {
            "type": "str",
            "default": "gathered",
            "choices": ["deleted", "gathered"],
        },
    }
