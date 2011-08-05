#!/usr/bin/python

# ================================================
# PYTHON->MACHINE ================================
# ================================================
import os
import sys
import json

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    def __init__(self, path_json_config):
        self.json_config = open(path_json_config)
        self.json_config = json.load(self.json_config)
        print self.json_config["packages"]

    def ensure_system_updated(self):
        return

    def install_packages(self):
        return
    
    def install_package(self, package):
        return

# ------------------------------------------------
# GLOBALS ----------------------------------------
# ------------------------------------------------
machine = Machine("machine.json")

# ------------------------------------------------
# MAIN -------------------------------------------
# ------------------------------------------------
def main():
    if os.getenv("USER") != "root":
        #print "fatal: You need to be root."
        #sys.exit(1)
        print "skipping root check"
    sys.exit(0)

