# -*- coding: utf-8 -*-
#
# jsonparser library script
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

from __future__ import absolute_import

import os
import unittest
import jsonparser
import logging
from pkg_resources import resource_filename

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')
logger.setLevel(logging.INFO)

class DeviceTest(unittest.TestCase):
    def test_parser(self):
        schema = resource_filename('tests','schema/sample1-schema.json')
        cfg = resource_filename('tests', 'config/sample1-cfg.json')
        obj = jsonparser.JSONParser(schema, cfg,
                                    extend_defaults= True, ref_resolver=True, parse_include=True,
                                    schema_dir=os.path.dirname(schema),
                                    cfg_dir=os.path.dirname(cfg),
                                    os_env=True, logger=logger)
        obj.print_cfg()
        obj.print_schema()
        #obj.dump_schema(outfile="final.schema")
        #obj.dump_cfg(outfile="final.cfg")




if __name__ == '__main__':
    unittest.main()
