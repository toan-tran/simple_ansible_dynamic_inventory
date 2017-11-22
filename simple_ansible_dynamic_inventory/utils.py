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
# OpenStack dynamic inventory for Ansible - Utils module
# This script will look for configuration file in the following order:
# .ansible/openstack_inventory.conf
# ~/ansible/openstack_inventory.conf
# /etc/ansible/openstack_inventory.conf
#

from ConfigParser import ConfigParser
import json
import os
import string

from novaclient import client

CONF_FILES = ["openstack_inventory.conf",
              ".ansible/openstack_inventory.conf",
              "~/.ansible/openstack_inventory.conf",
              "/etc/ansible/openstack_inventory.conf"]

HOST_INDICATORS = ["id", "name"]

DEFAULT_METADATA_NAMESPACE = "ansible:"

DEFAULT_KEY_FOLDER = "."


def get_config():
    """Get configs from known locations.
    If no file is present, no config is returned.
    :return: (dict) configs
             Empty dict if no file exists."""

    for cf in CONF_FILES:
        if os.path.exists(os.path.expanduser(cf)):
            parser = ConfigParser()
            configs = dict()
            parser.read(os.path.expanduser(cf))
            for sec in parser.sections():
                configs[sec] = dict(parser.items(sec))
            return configs
    return {}


def get_template(configs):
    "Get inventory template from template file."
    inventory = {"_meta": {
                   "hostvars": {}
                 }}
    if "Template" in configs:
        if "template_file" in configs["Template"]:
            with open(os.path.abspath(os.path.expanduser(configs["Template"]["template_file"]))) as f:
                template = json.load(f)
                inventory.update(template)
    return inventory

    
def get_client(configs):
    authentication = configs.get('Authentication', {})
    os_identity_api_version = os.environ.get('OS_VERSION',
                                             os.environ.get('OS_IDENTITY_API_VERSION',
                                             authentication.get('os_version',2)))
    os_auth_url = os.environ.get('OS_AUTH_URL',
                                 authentication.get('os_auth_url'))
    if not os_auth_url:
        raise Exception("ERROR: OS_AUTH_URL is not set")
    os_username = os.environ.get('OS_USERNAME',
                                 authentication.get('os_username'))
    if not os_username:
        raise Exception("ERROR: OS_USERNAME is not set")
    os_password = os.environ.get('OS_PASSWORD',
                                 authentication.get('os_password'))
    if not os_password:
        raise Exception("ERROR: OS_PASSWORD is not set")

    os_tenant_id = os.environ.get('OS_TENANT_ID',
                                  os.environ.get('OS_PROJECT_ID',
                                  authentication.get('os_tenant_id',
                                  authentication.get('os_project_id'))))
    if not os_tenant_id:
        raise Exception("ERROR: No OS_TENANT_ID or OS_PROJECT_ID is set")

    os_user_domain_name = os.environ.get('OS_USER_DOMAIN_NAME', 'default')

    if os_identity_api_version == '2':
        nova = client.Client('2.1', os_username, os_password,
                             os_tenant_id, os_auth_url)
    else:
        nova = client.Client('2.1', os_username, os_password,
                             os_tenant_id, os_auth_url,
                             user_domain_name=os_user_domain_name)
    return nova
