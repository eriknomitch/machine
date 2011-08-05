#!/usr/bin/python

# ================================================
# PYTHON->MACHINE ================================
# ================================================
import os
import sys
import json
import apt

# ------------------------------------------------
# CLASS->PACKAGE ---------------------------------
# ------------------------------------------------
class Package:
    def __init__(self, name):
        self.name = name

    def install(self, cache):
        print "ensuring package: \""+self.name+"\""
        self.package = cache[self.name]
        self.package.mark_install()
        return

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    def __init__(self, path_json_config):
        self.json_config = open(path_json_config)
        self.json_config = json.load(self.json_config)

        self.packages = map(lambda package_name: Package(package_name), self.json_config["packages"])
        self.cache = apt.Cache()

    def ensure_system_updated(self):
        return

    def setup_packages(self):
        print "updating: apt cache"
        self.cache.update()

        for package in self.packages:
            package.install(self.cache)

        self.cache.commit()
    
    def setup(self):
        self.setup_packages()
        return

# ------------------------------------------------
# GLOBALS ----------------------------------------
# ------------------------------------------------
machine = Machine("tests/machine.json")

# ------------------------------------------------
# MAIN -------------------------------------------
# ------------------------------------------------
def main():
    if os.getenv("USER") != "root":
        print "fatal: You need to be root."
        sys.exit(1)

    machine.setup()
    sys.exit(0)

main()

