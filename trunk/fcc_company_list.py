# encoding=utf-8

import sys
import os.path
import xml.dom.minidom as dom
import domutil
    

def load(filename):
    config = dom.parse(filename)
    grantees = config.getElementsByTagName('grantee_code')

    return [domutil.node_text(node) for node in grantees]

