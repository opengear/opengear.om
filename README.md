# Ansible Collection - opengear.om

Documentation for the collection.

# Opengear OM Collection

The Ansible Opengear OM collection includes a variety of Ansible content to help automate the management of Opengear OM network appliances.

### Supported connections
The Ansible OM collection supports ``httpapi``  connections.

## Included content

<!--start collection content-->
### HTTPAPI plugins
Name | Description
--- | ---
opengear.om.om|Use Opengear REST API to run request on Opengear OM device

### Modules
Name | Description
--- | ---
opengear.om.om_auth|Configure remote authentication, authorization, accounting (AAA) servers.
opengear.om.om_conns|Read and manipulate the network connections on the Operations Manager appliance.
opengear.om.om_facts|Collect facts from OM devices
opengear.om.om_failover|Failover endpoint is to check failover status and retrieve / change failover settings.
opengear.om.om_groups|Retrieve or update group information.
opengear.om.om_pdu|Configure, monitor and control PDUs connected to the device.
opengear.om.om_physifs|Read and manipulate the network physical interfaces on the Operations Manager appliance.
opengear.om.om_ports|Configuring and viewing ports information
opengear.om.om_services|Used for working with the properties of the various services running on the system.
opengear.om.om_static_routes|Configuring and viewing static routes
opengear.om.om_system|Used for configuring and accessing information about the Operations Manager appliance itself.
opengear.om.om_users|Retrieve and update user information.

<!--end collection content-->
## Installing this collection

You can install the Opengear OM collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install opengear.om

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: opengear.om
```
## Using this collection


This collection includes [network resource modules](https://docs.ansible.com/ansible/latest/network/user_guide/network_resource_modules.html).

### Using modules from the Opengear OM collection in your playbooks

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `opengear.om.om_users`.
The following example task replaces configuration changes in the existing configuration on a Opengear OM network device, using the FQCN:

```yaml
---
  - name: Replace device configuration of users.
    openear.om.om_users:
      config:
        - name: user1
          enabled: true
          no_password: true
          groups:
          - group1
      state: replaced

```

### See Also:

* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Opengear OM collection repository](https://github.com/opengear/opengear.om). 

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.

### Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## More information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [Opengear OM REST API](https://ftp.opengear.com/download/api/operations_manager/og-rest-api-specification-v2-ngcs.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
