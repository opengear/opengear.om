# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible_collections.opengear.ng.plugins.module_utils.argspec.ports_config import PortsConfigArgs
from ansible_collections.opengear.ng.plugins.module_utils.utils import utils

# Read-only fields returned by the API that must not appear in gathered facts
_READONLY_FIELDS = frozenset({
    "device", "status", "available_baudrates", "available_pinouts",
    "sessions", "pdu_outlets",
})


class PortsConfigFacts(object):
    """
    Retrieves and parses port configuration facts from Opengear devices.
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = PortsConfigArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection):
        return connection.get(None, 'ports')['ports']

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for ports_config.

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        objs = []
        for instance in data:
            if instance:
                obj = self.render_config(self.generated_spec, instance)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('ports_config', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['ports_config'] = params['config']

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """Render config as dictionary, filtering to spec keys and removing empties.

        Read-only API fields (device, status, available_*, sessions, pdu_outlets)
        are excluded because they are not in the argspec.
        """
        config = deepcopy(spec)
        for option in config.keys():
            if option in conf and option not in _READONLY_FIELDS:
                config[option] = conf[option]
        return utils.remove_empties(config)
