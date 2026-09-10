# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from ansible_collections.opengear.ng.plugins.module_utils.argspec.pdu_config import PduConfigArgs
from ansible_collections.opengear.ng.plugins.module_utils.utils import utils

# Fields on each outlet that belong to configuration (name/port mapping).
# status, status_timestamp, last_action, last_action_timestamp, and id are
# runtime/read-only and are surfaced instead by the pdu_status module.
_OUTLET_CONFIG_FIELDS = ("number", "name", "port")


class PduConfigFacts(object):
    """
    Retrieves and parses PDU configuration facts from Opengear devices.
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = PduConfigArgs.argument_spec
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
        return connection.get(None, 'pdus')['pdus']

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for pdu_config.

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

        ansible_facts['ansible_network_resources'].pop('pdu_config', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['pdu_config'] = params['config']

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """Render config as dictionary, filtering to spec keys.

        Outlet entries are narrowed to their configuration fields; the
        device includes read-only status fields on each outlet that are
        not part of pdu_config.
        """
        config = deepcopy(spec)
        for option in config.keys():
            if option in conf:
                config[option] = conf[option]

        if config.get('outlets'):
            config['outlets'] = [
                {field: outlet.get(field) for field in _OUTLET_CONFIG_FIELDS}
                for outlet in config['outlets']
            ]

        return utils.remove_empties(config)
