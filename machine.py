#!/usr/bin/python

# ================================================
# PYTHON->MACHINE ================================
# ================================================
import os
import sys
import json
import apt
import subprocess
import crypt

# ------------------------------------------------
# CLASS->USER ------------------------------------
# ------------------------------------------------
class User:
    def __init__(self, json):
        self.json           = json
        self.name           = json["name"]
        self.password       = json["password"]
        self.password_crypt = crypt.crypt(self.password, self.name)

    def create(self):
        useradd_arguments = ["useradd", "--create-home", self.name, "--password", self.password_crypt]
        useradd_process = subprocess.Popen(useradd_arguments)

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

        self.cache.open(None)
    
        # CHECK: This isn't tested...
        # CHECK: Should we reboot here? What if we upgrade a kernel...
        print "upgrading: apt packages"
        self.cache.upgrade(True)

        for package in self.packages:
            package.install(self.cache)

        self.cache.commit()

    def setup_users(self):
        self.users = map(lambda user_json: User(user_json), self.json_config["users"])

        for user in self.users:
            user.create()
            
        return
    
    def setup(self):
        self.setup_packages()
        self.setup_users()
        # CHECK: Reboot here?
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

