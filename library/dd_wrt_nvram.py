#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Eric Miller <sosheskaz.github.io@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: group
author:
- Eric Miller (@sosheskaz)
version_added: "N/A"
short_description: Configure DD-WRT nvram settings
requirements:
    - nvram
description:
    - Manage settings set with NVRAM on DD-WRT
options:
    key:
        description:
            - Name of the parameter to operate on
        required: true
    value:
        description:
            - Value to set the parameter to
        required: true
    state:
        description:
            - set or unset the variable.
        required: false
        default: 'present'
        choices: ['present', 'absent', 'get']
    commit:
        description:
            - Save all changed variables to NVRAM
        required: false
        default: yes
        choices: ['yes', 'no']
'''

EXAMPLES = '''
- name: Set /opt automount to a UUID
  dd_wrt_nvram:
    key: usb_mntopt
    value: D273628F-675C-45C1-AA52-98278D3948B7

- name: Remove a custom key
  dd_wrt_nvram:
    key: my_key
    state: absent

- name: Get the value of a key
  dd_wrt_nvram:
    key: my_key
    state: absent
'''

import subprocess

from ansible.module_utils.basic import AnsibleModule, load_platform_subclass


def get_value(key):
    value = subprocess.check_output(['nvram', 'get', key])
    if value.endswith('\n'):
        value = value[:-1]
    if value == '':
        value = None
    return {
        'key': key,
        'value': value
    }


def set_value(key, value, check_mode):
    current_value = get_value(key)['value']
    results = {
        'key': key,
        'old_value': current_value
    }

    if current_value != value:
        if not check_mode:
            subprocess.call(['nvram', 'set', '{}={}'.format(key, value)])
            current_value = get_value(key)['value']
        results['changed'] = True

    results['new_value'] = current_value
    return results


def rm_value(key, check_mode):
    current_value = get_value(key)
    results = {
        'key': key,
        'old_value': current_value
    }

    if current_value is not None:
        if not check_mode:
            subprocess.call(['nvram', 'unset', key])
            current_value = get_value(key)
        results['changed'] = True

    results['new_value'] = None
    return results


def commit(check_mode):
    if not check_mode:
        subprocess.check_call(['nvram', 'commit'])
    return {
        'committed': True,
        'changed': True
    }


def main():
    required_if = [['state', 'present', ['value']]]
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present',
                       choices=['absent', 'get', 'present', 'show']),
            key=dict(type='str', required=True),
            value=dict(type='str'),
            commit=dict(type=bool, default=False)
        ),
        required_if=required_if,
        supports_check_mode=True,
    )

    results = {
        'changed': False,
        'committed': False
    }

    if module.params['state'] == 'get':
        results.update(get_value(module.params['key']))

    if module.params['state'] == 'present':
        if '=' in module.params['value']:
            module.fail_json(
                msg='You tried to set a value with "=" in it. This is not supported by this module.')
            return

        results.update(set_value(module.params['key'],
                                 module.params['value'],
                                 module.check_mode))

    if module.params['state'] == 'absent':
        results.update(rm_value(module.params['key'], module.check_mode))

    if module.params['commit']:
        results.update(commit(module.check_mode))

    module.exit_json(**results)


if __name__ == '__main__':
    main()
