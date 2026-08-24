# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class FailoverArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the failover module.
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "config": {
            "type": "dict",
            "options": {
                "enabled": {"type": "bool"},
                "probe_physif": {"type": "str"},
                "probe_address": {"type": "str"},
                "probe_address_2": {"type": "str"},
                "dormant_dns": {"type": "bool"},
                "failover_physif": {"type": "str"},
            },
        },
        "state": {
            "type": "str",
            "default": "merged",
            "choices": [
                "merged",
                "replaced",
                "overridden",
                "gathered",
                "rendered",
            ],
        },
    }  # pylint: disable=C0301
