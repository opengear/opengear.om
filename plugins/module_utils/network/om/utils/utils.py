# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

structure = """{
  "system": {
    "hostname": ["system_hostname", "hostname"],
    "banner": ["system_banner", "banner"],
    "webui_session_timeout": ["system_webui_session_timeout", "timeout"],
    "cli_session_timeout": ["system_cli_session_timeout", "timeout"],
    "system_authorized_keys": ["system_authorized_keys"],
    "ssh_port": ["system_ssh_port", "port"],
    "timezone": ["system_timezone", "timezone"],
    "time": ["time", "time"],
    "admin_info": ["system_admin_info"]
  }
}"""

def get_restapi_body_structure():
    return json.loads(structure)

def command_builder(data, path, instance_id=None, delete_exceptions=None, method=None):
    """
    A command builder that produces PUT, POST or DELETE commands depending on the parameters provided.
    :param method: A method that may be PUT, POST or DELETE. None by default.
    :param data: The data forming the body of the request.
    :param path: The endpoint URI path.
    :param instance_id: The id value of the instance.
    :param delete_exceptions: Any instance ids that may not be deleted.
    :return: A PUT command if id and data are provided, a DELETE command if no data is provided and provided id value
     is not an exception, a POST request if data is provided and an id value is not, or None if command isn't valid.
    """
    if method:
        return {'data': data, 'path': path, 'method': method}
    if instance_id:
        path += instance_id
        if data:
            method = 'PUT'
        elif not delete_exceptions or instance_id not in delete_exceptions:
            method = 'DELETE'
    elif data:
        method = 'POST'
    if method:
        return {'data': data, 'path': path, 'method': method}


def find_instance_id(name_id_map, name, instance):
    """
    Finds the id value of a configuration instance (user, group, conn, etc) using a given name value. If the instance
    has an id value, this will be returned. Otherwise, the name value of the instance will be used to search a
    name-id map.
    :param name_id_map: The mapping of name values to id values.
    :param name: The name key string (username, groupname, etc).
    :param instance: The configuration instance for which the id value belongs to.
    :return: An id value. If instance does not contain either an id or name value, or if the map does not contain a
    matching id value, None is returned.
    """
    instance_id = None
    if instance:
        instance_id = instance.pop('id', None)
        if instance_id and instance_id not in name_id_map.values():
            instance_id = None
        if not instance_id and name in instance and instance[name] in name_id_map:
            instance_id = name_id_map[instance[name]]
    return instance_id


def is_subset(want, have):
    if len(want) > len(have):
        return False
    for key in want.keys():
        if key not in have:
            return False
        if isinstance(want[key], list) and isinstance(have[key], list) and not set(want[key]).issubset(set(have[key])):
            return False
        if isinstance(want[key], dict) and isinstance(have[key], dict) and not is_subset(want[key], have[key]):
            return False
        if want[key] != have[key]:
            return False
    return True
