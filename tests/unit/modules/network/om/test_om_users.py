# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.opengear.om.tests.unit.compat.mock import patch
from ansible_collections.opengear.om.plugins.modules import (
    om_users,
)
from ansible_collections.opengear.om.tests.unit.modules.utils import (
    set_module_args,
)
from .om_module import TestOmModule, load_fixture


class TestOmUsersModule(TestOmModule):

    module = om_users

    def setUp(self):
        super(TestOmUsersModule, self).setUp()

        self.mock_get_device_data = patch(
            "ansible_collections.opengear.om.plugins.module_utils.network.om."
            "facts.users.users.UsersFacts.get_device_data"
        )
        self.get_device_data = self.mock_get_device_data.start()

        self.mock_get_resource_connection_config = patch(
            "ansible_collections.ansible.netcommon.plugins.module_utils.network.common.cfg.base.get_resource_connection"
        )
        self.get_resource_connection_config = (
            self.mock_get_resource_connection_config.start()
        )

        self.mock_get_resource_connection_facts = patch(
            "ansible_collections.ansible.netcommon.plugins.module_utils.network.common.facts.facts.get_resource_connection"
        )
        self.get_resource_connection_facts = (
            self.mock_get_resource_connection_facts.start()
        )

    def tearDown(self):
        super(TestOmUsersModule, self).tearDown()
        self.mock_get_device_data.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_resource_connection_config.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture("om_users_config.cfg")

        self.get_device_data.side_effect = load_from_file

    def test_om_users_merged(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1", username="user1-modified", description="This user was changed", enabled=False, no_password=True, groups=["g2"]),
                    dict(username="user3", description="This user was added", enabled=True, no_password=True, groups=["g1"])
                ],
                state="merged",
            )
        )

        commands = [
                dict(path='users/users-1',
                     data=dict(user=dict(username="user1-modified", description="This user was changed", enabled=False,
                               no_password=True, ssh_password_enabled=True, password=None,
                               hashed_password="$5$vqpQsIj./5/2OOBo$tTUYAJaEqbZYf4aipKicPF5bpkkGSEqtBy3t4dylp0/",
                               groups=["g2", "g1"])),
                     method='PUT'),
                dict(path='users/',
                     data=dict(user=dict(username="user3", description="This user was added", enabled=True, no_password=True,
                               groups=["g1"])),
                     method='POST')]
        self.execute_module(changed=True, commands=commands)

    def test_om_users_merged_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(username="user1", enabled=True, hashed_password="$5$vqpQsIj./5/2OOBo$tTUYAJaEqbZYf4aipKicPF5bpkkGSEqtBy3t4dylp0/", groups=["g1"]),
                    dict(username="user2", enabled=True, no_password=True, groups=["g1"])
                ],
                state="merged",
            )
        )

        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_om_users_replaced(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1", username="user1-modified", description="This user was changed", enabled=False,
                         no_password=True, groups=["g2"]),
                    dict(username="user3", description="This user was added", enabled=True, no_password=True,
                         groups=["g1"])
                ],
                state="replaced",
            )
        )

        commands = [
            dict(path='users/users-1',
                 data=dict(user=dict(username="user1-modified", description="This user was changed", enabled=False,
                                     no_password=True, groups=["g2"])),
                 method='PUT'),
            dict(path='users/',
                 data=dict(
                     user=dict(username="user3", description="This user was added", enabled=True, no_password=True,
                               groups=["g1"])),
                 method='POST')]
        self.execute_module(changed=True, commands=commands)

    def test_om_users_replaced_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(username="user1", enabled=True,
                         hashed_password="$5$vqpQsIj./5/2OOBo$tTUYAJaEqbZYf4aipKicPF5bpkkGSEqtBy3t4dylp0/",
                         groups=["g1"]),
                    dict(username="user2", enabled=True, no_password=True, groups=["g1"])
                ],
                state="replaced",
            )
        )

        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_om_users_overridden(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1", username="user1-modified", description="This user was changed", enabled=False,
                         no_password=True, groups=["g2"]),
                    dict(username="user3", description="This user was added", enabled=True, no_password=True,
                         groups=["g1"])
                ],
                state="overridden",
            )
        )

        commands = [
            dict(path='users/users-2', data=None, method='DELETE'),
            dict(path='users/users-1',
                 data=dict(user=dict(username="user1-modified", description="This user was changed", enabled=False,
                                     no_password=True, groups=["g2"])),
                 method='PUT'),
            dict(path='users/',
                 data=dict(
                     user=dict(username="user3", description="This user was added", enabled=True, no_password=True,
                               groups=["g1"])),
                 method='POST')]
        self.execute_module(changed=True, commands=commands)

    def test_om_users_overridden_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(username="user1", enabled=True,
                         hashed_password="$5$vqpQsIj./5/2OOBo$tTUYAJaEqbZYf4aipKicPF5bpkkGSEqtBy3t4dylp0/",
                         groups=["g1"]),
                    dict(username="user2", enabled=True, no_password=True, groups=["g1"])
                ],
                state="overridden",
            )
        )

        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_om_users_deleted(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1"),
                    dict(username="user2"),
                    dict(username="user3")
                ],
                state="deleted",
            )
        )

        commands = [
            dict(path='users/users-2', data=None, method='DELETE')
        ]
        self.execute_module(changed=True, commands=commands)

    def test_om_users_rendered(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1", username="user1-modified", description="This user was changed", enabled=False,
                         no_password=True, groups=["g2"]),
                    dict(username="user3", description="This user was added", enabled=True, no_password=True,
                         groups=["g1"])
                ],
                state="rendered",
            )
        )

        commands = []

        self.execute_module(changed=False, commands=commands)

    def test_om_users_gathered(self):
        set_module_args(
            dict(
                config=[
                    dict(id="users-1", username="user1-modified", description="This user was changed", enabled=False,
                         no_password=True, groups=["g2"]),
                    dict(username="user3", description="This user was added", enabled=True, no_password=True,
                         groups=["g1"])
                ],
                state="gathered",
            )
        )

        commands = []

        self.execute_module(changed=False, commands=commands)
