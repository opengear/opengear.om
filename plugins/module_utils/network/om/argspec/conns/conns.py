#
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the om_conns module
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ConnsArgs(object):  # pylint: disable=R0903
    """The arg spec for the om_conns module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'elements': 'dict',
                                'options': {'id': {'type': 'str'},
                                            'ipv4_static_settings': {'options': {'address': {'type': 'str'},
                                                                                 'broadcast': {'type': 'str'},
                                                                                 'dns1': {'type': 'str'},
                                                                                 'dns2': {'type': 'str'},
                                                                                 'gateway': {'type': 'str'},
                                                                                 'netmask': {'type': 'str'}},
                                                                     'type': 'dict'},
                                            'ipv6_static_settings': {'options': {'address': {'type': 'str'},
                                                                                 'dns1': {'type': 'str'},
                                                                                 'dns2': {'type': 'str'},
                                                                                 'gateway': {'type': 'str'},
                                                                                 'prefix_length': {'type': 'str'}},
                                                                     'type': 'dict'},
                                            'mode': {'type': 'str'},
                                            'name': {'type': 'str'},
                                            'physif': {'type': 'str'}},
                                'type': 'list'},
                     'state': {'choices': ['merged',
                                           'replaced',
                                           'overridden',
                                           'deleted',
                                           'gathered',
                                           'rendered'],
                               'default': 'merged',
                               'type': 'str'}}  # pylint: disable=C0301
