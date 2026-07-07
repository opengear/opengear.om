# Opengear NG Ansible Collection

The Opengear NG Collection includes a variety of Ansible content to help
automate the management of Opengear network appliances.

![Main CI Status][main-ci-status]

## Supported Products
The Opengear NG collection supports the following Opengear product families:

- OM12xx
- OM13xx
- OM22xx
- CM80xx
- CM81xx

## Modules
| Name                             | Description                                                                                          |
| -------------------------------- | ---------------------------------------------------------------------------------------------------- |
| opengear.ng.auth                 | Manage remote authentication, authorization, and accounting (AAA) configuration.                     |
| opengear.ng.conns                | Manage network connection configuration.                                                             |
| opengear.ng.config_diff          | Compare current device configuration to file.                                                        |
| opengear.ng.config_export        | Export current device configuration to file.                                                         |
| opengear.ng.config_import        | Import device configuration from file merging with current device configuration.                     |
| opengear.ng.config_restore       | Restore device configuration from file.                                                              |
| opengear.ng.facts                | Gather device information and network resource configuration facts.                                  |
| opengear.ng.failover             | Manage failover configuration and retrieve failover status.                                          |
| opengear.ng.firmware_upgrade     | Manage firmware upgrades on Opengear devices.                                                        |
| opengear.ng.groups               | Manage user group configuration.                                                                     |
| opengear.ng.pdu                  | Manage PDUs connected to the device, including configuration, monitoring, and control.               |
| opengear.ng.physifs              | Manage physical network interface configuration.                                                     |
| opengear.ng.ports                | Manage serial port configuration.                                                                    |
| opengear.ng.services             | Manage system service configuration.                                                                 |
| opengear.ng.static_routes        | Manage static route configuration.                                                                   |
| opengear.ng.system               | Manage device system configuration and retrieve device information.                                  |
| opengear.ng.user_authorized_keys | Manage configuration of user authorized keys on Opengear devices.                                    |
| opengear.ng.users                | Manage user configuration.                                                                           |

## Connections
Modules in this collection use the Ansible `httpapi` connection plugin by default
to communicate with Opengear devices via the REST API.

The following modules are exceptions that require `ansible_connection: ssh` to
be used and do not support the default `httpapi` connection.

- [opengear.ng.config_diff][]
- [opengear.ng.config_import][]

See each module's documentation and examples for configuration and usage
alongside httpapi modules.

[opengear.ng.config_diff]: plugins/modules/config_diff.py
[opengear.ng.config_import]: plugins/modules/config_import.py

## Installing The Collection

You can install the latest release of this collection with the Ansible Galaxy CLI:
```
ansible-galaxy collection install opengear.ng
```
You can also include it in a `requirements.yml` file and install it with
`ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: opengear.ng
```

> **Developers:** See [CONTRIBUTING.md](CONTRIBUTING.md) for local development installation instructions.


## Using NG Collection

This collection includes [network resource modules](https://docs.ansible.com/ansible/latest/network/user_guide/network_resource_modules.html).

### Authentication

This collection uses the Ansible `httpapi` connection plugin for authentication.

Authentication is handled by the Opengear REST API using standard Ansible connection variables.

### Inventory Example

To connect to an Opengear device, define hosts in `inventory.yml`.

```yaml
all:
  children:
    opengear:
      hosts:
        my-device:
          ansible_host: 192.168.1.1
      vars:
        ansible_connection: httpapi
        ansible_network_os: opengear.ng.http_api  # required - httpapi plugin to use for this collection
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
        ansible_user: "{{ opengear_user }}"
        ansible_password: "{{ opengear_password }}"
```

### Playbook Example

You can call modules by their Fully Qualified Collection Namespace (FQCN) such
as `opengear.ng.users`.

The following example task replaces configuration for an entity in the existing
configuration of an Opengear network device, using the FQCN:

```yaml
---
- name: Example playbook for managing groups
  hosts: opengear
  gather_facts: false

  tasks:
    - name: Replace device configuration of group1.
      opengear.ng.groups:
        config:
          - name: group1
            enabled: true
            description: This is an example group
            members: []
            access_rights: ['web_ui', 'pmshell']
            ports: ['port-1','port-2']
        state: replaced
```

### Further Examples

For more examples of opengear.ng module usage, see [Examples](examples/).

For general Ansible collection usage, see [Using Ansible Collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html).

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md)
before submitting a pull request.

### Code of Conduct
This collection follows the Ansible project's [Code of Conduct][].
Please read and familiarize yourself with this document.

[Code of Conduct]: https://docs.ansible.com/ansible/devel/community/code_of_conduct.html

## More information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [Opengear OM REST API](https://ftp.opengear.com/download/opengear_appliances/OM/OM2200/current/documentation/og-rest-api-specification-v2-ngcs.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.

[main-ci-status]: https://img.shields.io/github/actions/workflow/status/opengear/ansible-ng/.github%2Fworkflows%2Fmain.yml?branch=main
