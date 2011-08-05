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
        self.password_crypt = crypt.crypt(self.password, self.name) # CHECK: Is this salt what it's supposed to be (self.name)?

    def create(self):
        useradd_arguments = ["useradd", "--create-home", "--password", self.password_crypt, self.name]
        useradd_process = subprocess.Popen(useradd_arguments)

# ------------------------------------------------
# CLASS->PACKAGE ---------------------------------
# ------------------------------------------------
class Package:
    def __init__(self, name):
        self.name = name

    def install(self, cache):
        print "installing:package:\""+self.name+"\""
        if self.name in cache.keys():
            self.package = cache[self.name]
            self.package.mark_install()
        else:
            print "warning:package-not-found:\""+self.name+"\""

# ------------------------------------------------
# CLASS->GEM -------------------------------------
# ------------------------------------------------
class Gem:
    def __init__(self, name):
        self.name = name

    def install(self):
        # FIX: Download latest from source and setup.rb
        #ln_arguments = ["ln", "-s", "/usr/bin/gem1.8", "/usr/bin/gem"]
        print "installing:gem: \""+self.name+"\""
        return

# ------------------------------------------------
# CLASS->FILE ------------------------------------
# ------------------------------------------------
class File:
    def __init__(self, json):
        self.json = json
        self.name = json["name"]

    def install(self):
        print "installing:file: \""+self.name+"\""
        return

# ------------------------------------------------
# CLASS->WEBSITE ---------------------------------
# ------------------------------------------------
class Website:
    def __init__(self, domain):
        self.domain = domain

    def install(self, cache):
        return

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    def __init__(self, path_json_config):
        self.json_config = open(path_json_config)
        self.json_config = json.load(self.json_config)

        self.packages = map(lambda package_name: Package(package_name), self.json_config["packages"])
        self.gems     = map(lambda gem_name: Gem(gem_name), self.json_config["gems"])
        self.files    = map(lambda json: File(json), self.json_config["files"])
        self.websites = map(lambda json: Website(json), self.json_config["websites"])

        self.cache = apt.Cache()

    # --------------------------------------------
    # SETUP->UTILITY -----------------------------
    # --------------------------------------------
    def setup_standard(self, array):
        for element in array:
            element.install()

    # --------------------------------------------
    # SETUPS -------------------------------------
    # --------------------------------------------
    def setup_gems(self):
        self.setup_standard(self.gems)

    def setup_files(self):
        self.setup_standard(self.files)

    def setup_websites(self):
        self.setup_standard(self.websites)
    
    def setup_packages(self):
        print "updating:apt:cache"
        self.cache.update()

        self.cache.open(None)
    
        # CHECK: Should we reboot here? What if we upgrade a kernel...
        print "upgrading:apt:packages"
        self.cache.upgrade(True)

        for package in self.packages:
            package.install(self.cache)

        self.cache.commit()

    def setup_users(self):
        self.users = map(lambda user_json: User(user_json), self.json_config["users"])

        for user in self.users:
            user.create()

    # --------------------------------------------
    # SETUP --------------------------------------
    # --------------------------------------------
    def setup(self):
        self.setup_users()
        self.setup_packages()
        self.setup_files()
        self.setup_gems()
        self.setup_websites()
        #os.system("reboot")

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

