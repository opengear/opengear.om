# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class PduConfigArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the pdu_config module.
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
                "driver": {
                    "type": "dict",
                    "options": {
                        "id": {"type": "str"},
                        "name": {"type": "str"},
                    },
                },
                "method": {
                    "type": "str",
                    "choices": ["powerman", "shell", "snmp"],
                },
                "monitor": {"type": "bool"},
                "powerman": {
                    "type": "dict",
                    "options": {
                        "id": {"type": "str"},
                        "username": {"type": "str"},
                        "password": {"type": "str", "no_log": True},
                        "port": {"type": "str"},
                    },
                },
                "shell": {
                    "type": "dict",
                    "options": {
                        "id": {"type": "str"},
                        "username": {"type": "str"},
                        "password": {"type": "str", "no_log": True},
                        "port": {"type": "str"},
                    },
                },
                "snmp": {
                    "type": "dict",
                    "options": {
                        "id": {"type": "str"},
                        "protocol": {"type": "str", "choices": ["UDP", "TCP"]},
                        "address": {"type": "str"},
                        "port": {"type": "int"},
                        "version": {"type": "str", "choices": ["1", "2c", "3"]},
                        "community": {"type": "str"},
                        "auth_protocol": {
                            "type": "str",
                            "choices": [
                                "SHA", "MD5", "SHA-512", "SHA-384", "SHA-256", "SHA-224",
                            ],
                        },
                        "auth_password": {"type": "str", "no_log": True},
                        "security_name": {"type": "str"},
                        "engine_id": {"type": "str"},
                        "privacy_protocol": {
                            "type": "str",
                            "choices": ["DES", "AES", "AES-192", "AES-256"],
                        },
                        "privacy_password": {"type": "str", "no_log": True},
                        "security_level": {
                            "type": "str",
                            "choices": ["noAuthNoPriv", "authNoPriv", "authPriv"],
                        },
                    },
                },
                "outlets": {
                    "type": "list",
                    "elements": "dict",
                    "options": {
                        "number": {"type": "int"},
                        "name": {"type": "str"},
                        "port": {"type": "str"},
                    },
                },
            },
        },
        "state": {
            "type": "str",
            "default": "merged",
            "choices": [
                "merged",
                "replaced",
                "overridden",
                "deleted",
                "gathered",
                "rendered",
            ],
        },
    }  # pylint: disable=C0301
