# Simple Ansible Dynamic OpenStack Inventories


## Introduction

This project provides a script that dynamically generate Ansible inventory content from OpenStack virtual machines or create VMs based on existing inventory.

Script:

  - openstack_inventory.py: Generates inventory from OpenStack platform


## Installation

  - Install depedencies
  
      ````
      pip install -r requirements.txt
      ````

  - The script will load configurations by looking for `openstack_inventory.conf` in following locations by the following order, first file found will be used.

      - Current folder
      - .ansible/
      - ~/.ansible/
      - /etc/ansible/

      If no configuration file is found, or no explicit value is set for a particular parameter, default values will be used, except for OpenStack credentials, which you must load as environment variables (e.g. source the OpenStack rc file).

  - You can use `openstack_inventory.conf.example` in the `examples` folder to create your own configuration file.


## Set up OpenStack platform

The script uses hosts' metadata to generate an inventory. The script uses all metadata that starts with `<metadata_namespace>`, with `<metadata_namespace>` is the value defined in your config. The default value is `ansible:` (no quote).

The `<metadata_namespace>` helps determine the VMs which belong to the playbook, and which do not.

To indicate a VM belongs to a group, put:

```
  <metadata_namespace>:groups=<group1>,<group2>,...
```

into its metadata. With `<metadata_namespace>` is `ansible:`, the command:

    ```
    nova meta vm1 set ansible:groups=apache2,ftp
    ```

will put VM into 2 groups: [apache2] and [ftp].

Every variable can also be put into the VM's metadata in the same way. Example:

    ```
    ansible:ansible_user=ubuntu
    ansible:ansible_private_key_file=my_key
    ansible:open_port=80
    ```


## Usage


  - Test the output of the script:

    ````
    python openstack_inventory.py
    ````

  - Test the script with Ansible:

    ````
    ansible -i openstack_inventory.py all -vvv -m ping
    ````


## Inventory Template

In addition to groups and variables that put into hosts' metadata, user can also add additional values into the inventory by using a template. The template is another JSON file that will be merged into the inventory, with values from hosts' metadata take priority.

*When is the template is useful ?*

Well, the most useful thing is to add group children into your inventory. You can do that by declaring all parent groups into your hosts' metadata, but it's nicer to have a hierarchy defined in the inventory, like with INI file. It's easier to manage and less error prone.

Another usecase is to add group variables. If you're like me, who still put variables into inventory (I do that a lot for my test/dev platforms - it's easier for the like of Jenkins to test different scenarios without updating OpenStack platform), then the template is here to do it.

However, for most usage, and if you have defined neat structures for different deployment, then you'll probably does not need a template. In that case just ignore the template_file variable in the config. By default no template is defined anyway.

Remember that these variables are considered as "Inventory vars/groups_vars", so they have lower priority than playbook group_vars (i.e. overriden by the latter).

Here is an example of a template:


````
{
  "webservices": {
    "children": ["apache2", "storage_nodes"],
    "vars": {
        "mysql_port": 3306,
        "web_port": 80,
        "ftp_port": 21
    }
  },
  "apache2": {
    "vars": {
        "https": "disabled"
  },
  "storage_nodes": {
    "children": ["mysql", "ftp"]
  }
}
````


## NOTE

  - If OpenStack credentials are not specified in the config file, user must specify them in environment variables (e.g. source openrc.sh). Environment variables always take precedence over config variables.

  - If 'ansible_private_key_file' is specified, make sur that all private keys are stored in the folder indicated by 'key_folder'.


## Ansible Dynamic Inventory documentation

  http://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html

