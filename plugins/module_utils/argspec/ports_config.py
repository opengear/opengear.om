# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class PortsConfigArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the ports_config module.
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
                "label": {"type": "str"},
                "mode": {
                    "type": "str",
                    "choices": [
                        "consoleServer",
                        "localConsole",
                        "disabled",
                    ],
                },
                "baudrate": {
                    "type": "str",
                    "choices": [
                        "50",
                        "75",
                        "110",
                        "134",
                        "150",
                        "200",
                        "300",
                        "600",
                        "1200",
                        "1800",
                        "2400",
                        "4800",
                        "9600",
                        "19200",
                        "38400",
                        "57600",
                        "115200",
                        "230400",
                    ],
                },
                "databits": {
                    "type": "str",
                    "choices": ["7", "8"],
                },
                "stopbits": {
                    "type": "str",
                    "choices": ["1", "2"],
                },
                "parity": {
                    "type": "str",
                    "choices": ["none", "odd", "even"],
                },
                "pinout": {
                    "type": "str",
                    "choices": ["X1", "X2", "USB"],
                },
                "logging_level": {
                    "type": "str",
                    "choices": [
                        "disabled",
                        "eventsOnly",
                        "eventsAndReceivedCharacters",
                        "eventsAndAllCharacters",
                    ],
                },
                "escape_char": {"type": "str"},
                "terminal_emulation": {
                    "type": "str",
                    "choices": ["vt100", "vt102", "vt220", "ansi", "linux"],
                },
                "kernel_debug": {"type": "bool"},
                "single_session": {"type": "bool"},
                "raw_tcp": {"type": "bool"},
                "dtr_mode": {
                    "type": "str",
                    "choices": ["alwayson", "activeuser", "alwaysoff"],
                },
                "ip_alias": {
                    "type": "list",
                    "elements": "dict",
                    "options": {
                        "ipaddress": {"type": "str"},
                        "interface": {"type": "str"},
                    },
                },
                "control_code": {
                    "type": "dict",
                    "options": {
                        "quit": {"type": "str"},
                        "chooser": {"type": "str"},
                        "power": {"type": "str"},
                        "portlog": {"type": "str"},
                        "pmhelp": {"type": "str"},
                        "break": {"type": "str"},
                    },
                },
            },
        },
        "state": {
            "type": "str",
            "default": "merged",
            "choices": ["merged", "replaced", "overridden", "gathered", "rendered"],
        },
    }  # pylint: disable=C0301
