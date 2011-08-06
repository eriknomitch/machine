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

    def install(self):
        useradd_arguments = ["useradd", "--create-home", "--password", self.password_crypt, self.name]
        useradd_process   = subprocess.Popen(useradd_arguments)

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
        print "installing:gem:\""+self.name+"\""
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
    def __init__(self, json):
        self.json   = json
        self.domain = json["domain"]
        self.name   = self.domain

    def virtual_host(self):
        return "<VirtualHost *:80>\n    DocumentRoot /var/www/"+self.name+"/public\n    ServerName www."+self.domain+"\n    ServerAlias "+self.domain+"\n    RailsEnv development\n    RailsBaseURI /\n    PassengerPoolIdleTime 0\n    RailsFrameworkSpawnerIdleTime 0\n    RailsFrameworkSpawnerIdleTime 0\n</VirtualHost>"

    def install(self):
        # cd /var/www && rails new && chown...
        print self.virtual_host()
        return

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    
    def __init__(self, path_json):
        self.json = open(path_json)
        self.json = json.load(self.json)

        self.packages = map(lambda name: Package(name), self.json["packages"])
        self.gems     = map(lambda name:     Gem(name), self.json["gems"])
        self.files    = map(lambda json:    File(json), self.json["files"])
        self.websites = map(lambda json: Website(json), self.json["websites"])
        self.users    = map(lambda json:    User(json), self.json["users"])

        self.cache = apt.Cache()
    
    # --------------------------------------------
    # SETUP->UTILITY -----------------------------
    # --------------------------------------------
    def setup_common(self, array):
        for element in array:
            element.install()

    # --------------------------------------------
    # SETUPS -------------------------------------
    # --------------------------------------------
    def setup_gems(self):
        # FIX: Download latest from source and setup.rb
        #ln_arguments = ["ln", "-s", "/usr/bin/gem1.8", "/usr/bin/gem"]
        self.setup_common(self.gems)

    def setup_files(self):
        # FIX: How will this handle tarballs?
        self.setup_common(self.files)

    def setup_websites(self):
        self.setup_common(self.websites)

    def setup_users(self):
        self.setup_common(self.users)

    def setup_databases(self):
        return
    
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

    # --------------------------------------------
    # SETUP --------------------------------------
    # --------------------------------------------
    def setup(self):
        #self.setup_users()
        #self.setup_packages()
        #self.setup_files()
        #self.setup_gems()
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

