#!/usr/bin/python

# ================================================
# PYTHON->MACHINE ================================
# ================================================
import os
import sys
import json

# ------------------------------------------------
# CLASS->PACKAGE ---------------------------------
# ------------------------------------------------
class Package:
    def __init__(self, name):
        self.name = name

    def install(self):
        print "installing: "+self.name
        return

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    def __init__(self, path_json_config):
        self.json_config = open(path_json_config)
        self.json_config = json.load(self.json_config)

        self.packages = map(lambda package_name: Package(package_name), self.json_config["packages"])

    def ensure_system_updated(self):
        return

    def setup_packages(self):
        for package in self.packages:
            package.install()
        return
    
    def setup(self):
        self.setup_packages()
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
        print "FIX: skipping root check"
    machine.setup()
    sys.exit(0)

main()

