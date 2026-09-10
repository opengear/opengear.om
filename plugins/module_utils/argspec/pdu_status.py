# -*- coding: utf-8 -*-
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class PduStatusArgs(object):  # pylint: disable=R0903
    """
    Argument specification for the pdu_status module.
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "state": {
            "type": "str",
            "default": "gathered",
            "choices": ["gathered"],
        },
    }
