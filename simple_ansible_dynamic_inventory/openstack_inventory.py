#!/usr//bin/env python
# Copyright Khanh-Toan TRAN <khtoantran@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# OpenStack dynamic inventory for Ansible
# This script provides inventory content for Ansible from OpenStack's VMs
# This script will look for configuration file in the following order:
# .ansible/openstack_inventory.conf
# ~/ansible/openstack_inventory.conf
# /etc/ansible/openstack_inventory.conf
#

import json
import os

from utils import *


def get_inventory(configs):
    """Generate an inventory from OpenStack platform.
    :param configs: (dict) Configuration
    :return: (dict) inventory
    """
    nova = get_client(configs)
    if not nova:
        raise Error("Cannot get OpenStack inventory. "
                    "Make sur that your OpenStack credential is well loaded. "
                    "(e.g. source openstack.rc")

    default_section = configs.get("Default", {})
    namespace = default_section.get("metadata_namespace",
                                    DEFAULT_METADATA_NAMESPACE)
    key_folder = default_section.get("key_folder", DEFAULT_KEY_FOLDER)
    key_folder = os.path.abspath(os.path.expanduser(key_folder))

    use_creation_key = default_section.get("use_creation_key",
                                           "false").lower() == "true"
    group_key = namespace + 'groups'

    server_list = [s for s in nova.servers.list() if group_key in s.metadata]

    # Ansible requires that if there is no host, the script must return {}
    if not server_list:
        return {}
    
    inventory = get_template(configs)

    for s in server_list:
        inventory_hostname = s.name
        metadata = s.metadata
        for group in metadata[group_key].split(','):
            if group not in inventory:
                inventory[group] = {"hosts": [inventory_hostname]}
            elif "hosts" not in inventory[group]:
                inventory[group]["hosts"] = [inventory_hostname]
            else:
                inventory[group]["hosts"].append(inventory_hostname)
        variables = {}
        # Take the first address as ansible_host by default.
        # If host has more than one addresses (e.g. multiple NICs,
        # Floating IP), then user should specify host address by
        # '<metadata_namespace>:ansible_host' key in metadata
        address = s.networks[s.networks.keys()[0]][0]
        variables['ansible_host'] = address
        for key, value in metadata.items():
            if key == (namespace + "ansible_private_key_file"):
                variables["ansible_private_key_file"] = os.path.join(
                                                        key_folder, value)
            elif (key.startswith(namespace) and (key != group_key)):
                keyname = key[len(namespace):]
                variables[keyname] = value
        if (("ansible_private_key_file" not in variables) and use_creation_key
            and not s.key_name):
            variables["ansible_private_key_file"] = os.path.join(
                                                    key_folder, s.key_name)
        inventory["_meta"]["hostvars"][inventory_hostname] = variables
    return inventory


def main():
    configs = get_config()
    inventory = get_inventory(configs)
    print json.dumps(inventory, indent=2)


if __name__ == "__main__":
    main()
