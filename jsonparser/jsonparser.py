# -*- coding: utf-8 -*-
#
# jsonparser library
#
# Copyright (C) 2018 Sathya Kuppuswamy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# @Author  : Sathya Kupppuswamy(sathyaosid@gmail.com)
# @History :
#            @v0.0 - Initial update
# @TODO    :
#
#

import json
import os
import re
from jsonschema import validators, validate, Draft4Validator, RefResolver
from jsonmerge import merge
import logging
import collections

# Make it work for Python 2+3 and with Unicode
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

def flatten_dict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + '.' + k, v) for k, v in flatten_dict(value).items() ]
        else:
            return [ (key, value) ]

    items = [ item for k, v in d.items() for item in expand(k, v) ]

    return dict(items)

class JSONParser(object):

    def _extend_with_default(self, validator_class):
        validate_properties = validator_class.VALIDATORS["properties"]

        def set_defaults(validator, properties, instance, schema):
            for property_, subschema in properties.items():
                if "default" in subschema and not isinstance(instance, list):
                    instance.setdefault(property_, subschema["default"])

            for error in validate_properties(
                    validator, properties, instance, schema,
            ):
                yield error

        return validators.extend(
            validator_class, {"properties": set_defaults},
        )

    def _sub_env(self, data={}, env_opt={}):

        if not data or not env_opt:
            return data

        def lookup(match):
            key = match.group(2)

            if key in env_opt.keys():
                return env_opt[key]

            return match.group(1)

        pattern = re.compile(r'(\${(.*)})')

        if isinstance(data, collections.Mapping):
            for key, value in data.iteritems():
                data[key] = self._sub_env(value, env_opt)
        elif isinstance(data, (list, tuple)):
            for index, value in enumerate(data):
                data[index] = self._sub_env(value, env_opt)
        elif isinstance(data, (str, unicode)):
            replaced = pattern.sub(lookup, data)
            if replaced is not None:
                return replaced
            else:
                return data

        return data

    def _sub_include(self, pattern, in_file, data, cfg_dir):

        if not data:
            return data

        def pattern_match(data):
            def lookup(match):
                if len(match.groups()) > 1:
                    new_inc_file = os.path.abspath(os.path.join(cfg_dir, match.group(2)))
                    if new_inc_file == os.path.abspath(in_file):
                        self.logger.warn("Warning: Circular dependency detected %s included in %s",
                                         new_inc_file, os.path.abspath(in_file))
                    else:
                        new_data, new_status = self._get_json_data(new_inc_file, True, cfg_dir, True)
                        if new_status is True:
                            if len(match.groups()) > 3 and match.group(4) is not None:
                                keys = match.group(4).split('/')
                                tmp = None
                                for key in keys:
                                    if key:
                                        tmp = new_data[key]
                                return tmp
                            else:
                                return new_data
                        else:
                            self.logger.warn("Not found valid data in %s", new_inc_file)

                return match.group(1)

            pattern =  r'(\$include <(.*\.json)(#/(.*))?>)'
            matchobj = re.search(pattern, data, 0)

            if matchobj:
                return lookup(matchobj)
            else:
                return data

        if isinstance(data, collections.Mapping):
            for key, value in data.iteritems():
                data[key] = self._sub_include(pattern, in_file, value, cfg_dir)
        elif isinstance(data, (list, tuple)):
            for index, value in enumerate(data):
                data[index] = self._sub_include(pattern, in_file, value, cfg_dir)
        elif isinstance(data, (str, unicode)):
            replaced = pattern_match(data)
            if replaced is not None:
                return replaced
            else:
                return data

        return data


    def _get_json_data(self, json_in, parse_include=False,
                       cfg_dir=os.getcwd(),
                       include_pattern=r'(\$include <(.*\.json)(#/(.*))?>)',
                       os_env=False, env_opt={}):

        data = ""
        status = False

        self.logger.debug("Json input type %s value: %s", type(json_in), json_in if type(json_in) is str else "...")

        if type(json_in) == str or type(json_in) == unicode:
            if os.path.exists(os.path.abspath(json_in)):
                with open(json_in) as data_file:
                    self.logger.debug("Reading %s file content", json_in)
                    data = json.load(data_file)
                    status = True
            else:
                self.logger.error("File %s does not exist", json_in)
                return data, status

        elif type(json_in) == dict:
            data = json_in
            status = True
        else:
            self.logger.warn("Not supported type")
            return data, status

        def sub_include(in_file, data, base_dir):
            if not data:
                return data

            replaced = self._sub_include(include_pattern, in_file, data, base_dir)
            return data if replaced is None else replaced

        def sub_env(data, opt):
            if not opt or not data:
                return data
            replaced = self._sub_env(data, opt)

            return data if replaced is None else replaced

        if parse_include is True:
            self.logger.debug("Include sub is enabeld")
            data = sub_include(json_in, data, cfg_dir)

        if os_env is True:
            self.logger.debug("OS Env sub is enabeld")
            data = sub_env(data, os.environ)

        if env_opt:
            self.logger.debug("Optional Env sub is enabled")
            data = sub_env(data, env_opt)

        self.logger.debug("Returning status %s", status)

        return data, status

    def __init__(self, schema, cfg, merge_list=[],
                 extend_defaults=False,
                 ref_resolver=False, schema_dir=os.getcwd(),
                 parse_include=False, include_pattern=r'(\$include <(.*\.json)(#/(.*))?>)',
                 cfg_dir=os.getcwd(),
                 os_env=False, opt_env={}, logger=None):
        """
        Wrapper class for JSON parsing.

        :param schema: Schema file assosiated with JSON file. Should be a valid file name or Dict with schema contents.
        :param cfg: Config file in JSON format. Should be a valid file name or Dict with schema contents.
        :param merge_list: List of Dict's or JSON file names.
        :param extend_defaults: Set True if you want to merge defaults from schema file.
        :param os_env: Set True if you want to do Environment variable substitute.
        :param opt_env: Environment variable dict.

         After processing the input, json file will be flatten need by using "separator".
        """
        self.logger = logger or logging.getLogger(__name__)
        self.data = None
        self.schema = None

        data, status = self._get_json_data(schema, parse_include, cfg_dir, include_pattern, os_env, opt_env)
        if status is False:
            self.logger.error("%s file not found\n" % schema)

        self.schema = data

        data, status = self._get_json_data(cfg, parse_include, cfg_dir, include_pattern, os_env, opt_env)
        if status is False:
            self.logger.error("%s file not found\n" % cfg)

        for entry in merge_list:
            mergedata, status = self._get_json_data(entry, parse_include, cfg_dir, include_pattern, os_env, opt_env)
            if status is False:
                self.logger.error("%s invalid merge files\n" % mergedata)

            result = merge(data, mergedata)

            data = result

        resolver = None

        if ref_resolver:
            resolver = RefResolver('file://' + os.path.abspath(schema_dir) + '/', self.schema)

        if extend_defaults is True:
            self._extend_with_default(Draft4Validator)(self.schema, resolver=resolver).validate(data)
        else:
            Draft4Validator(schema, resolver=resolver).validate(data)


        self.data = data

    def get_cfg(self):
        return self.data

    def get_schema(self):
        return self.schema

    def print_cfg(self, indent=4, sort_keys=True, sperators=(',', ': '), ensure_ascii=False):
        self.logger.info(json.dumps(self.data, indent=indent, sort_keys=sort_keys,
                                    separators=sperators, ensure_ascii=ensure_ascii))

    def print_schema(self, indent=4, sort_keys=True, sperators=(',', ': '), ensure_ascii=False):
        self.logger.info(json.dumps(self.schema, indent=indent, sort_keys=sort_keys,
                                    separators=sperators, ensure_ascii=ensure_ascii))

    def dump_cfg(self, out_file=None, indent=4, sort_keys=False, sperators=(',', ': '),
                 ensure_ascii=False, outfile=None):
        out_cfg = json.dumps(self.data, indent=indent, sort_keys=sort_keys, separators=sperators,
                             ensure_ascii=ensure_ascii)
        if outfile is not None and isinstance(outfile, basestring):
            with open(os.path.abspath(outfile), "w+") as fobj:
                fobj.write(out_cfg)

        return out_cfg

    def dump_schema(self, outfile=None, indent=4, sort_keys=False, sperators=(',', ': '),
                    ensure_ascii=False):
        out_schema = json.dumps(self.schema, indent=indent, sort_keys=sort_keys, separators=sperators,
                                ensure_ascii=ensure_ascii)
        if outfile is not None and isinstance(outfile, basestring):
            with open(os.path.abspath(outfile), "w+") as fobj:
                fobj.write(out_schema)

        return out_schema
