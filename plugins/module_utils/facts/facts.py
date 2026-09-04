# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# Copyright 2026 Opengear
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.ng.plugins.module_utils.facts.auth import AuthFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.base import FactsBase
from ansible_collections.opengear.ng.plugins.module_utils.facts.conns import ConnsFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.failover import FailoverFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.groups import GroupsFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.pdu import PduFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.physifs import PhysifsFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.ports_config import PortsConfigFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.services import ServicesFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.static_routes import StaticRoutesFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_config import SystemConfigFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_authorized_keys import SystemAuthorizedKeysFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_diskspace import SystemDiskspaceFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_firmware_upgrade import SystemFirmwareUpgradeFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_info import SystemInfoFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.system_time import SystemTimeFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.user_authorized_keys import UserAuthorizedKeysFacts
from ansible_collections.opengear.ng.plugins.module_utils.facts.users import UsersFacts

FACT_LEGACY_SUBSETS = {}

# Subsets excluded from 'all' must be requested explicitly.
OPT_IN_SUBSETS = frozenset([
    'system_authorized_keys',
    'system_firmware_upgrade',
    'user_authorized_keys',
])

FACT_RESOURCE_SUBSETS = dict(
    auth=AuthFacts,
    conns=ConnsFacts,
    failover=FailoverFacts,
    groups=GroupsFacts,
    pdu=PduFacts,
    physifs=PhysifsFacts,
    ports_config=PortsConfigFacts,
    services=ServicesFacts,
    static_routes=StaticRoutesFacts,
    system_authorized_keys=SystemAuthorizedKeysFacts,
    system_config=SystemConfigFacts,
    system_diskspace=SystemDiskspaceFacts,
    system_firmware_upgrade=SystemFirmwareUpgradeFacts,
    system_info=SystemInfoFacts,
    system_time=SystemTimeFacts,
    user_authorized_keys=UserAuthorizedKeysFacts,
    users=UsersFacts,
)


class Facts(FactsBase):
    """
    Entry point for fact gathering. Dispatches to the appropriate resource
    facts class based on the requested gather_network_resources subset.
    """

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for om

        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        if resource_facts_type and 'all' in resource_facts_type:
            resource_facts_type = [
                r for r in FACT_RESOURCE_SUBSETS if r not in OPT_IN_SUBSETS
            ]
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(FACT_RESOURCE_SUBSETS, resource_facts_type, data)

        if self.VALID_LEGACY_GATHER_SUBSETS:
            self.get_network_legacy_facts(FACT_LEGACY_SUBSETS, legacy_facts_type)

        return self.ansible_facts, self._warnings
