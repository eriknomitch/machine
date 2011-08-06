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
        useradd_process   = subprocess.call(useradd_arguments)

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
        gem_arguments = ["gem", "install", self.name]
        gem_process   = subprocess.call(gem_arguments)

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
        # CHECK: Do we even need self.name? Should everything be based on the domain instead in case we have foo.com and foo.org which are different sites?
        self.json     = json
        self.domain   = json["domain"]
        self.database = json["database"]
        self.name     = json["name"] # FIX: Extract this with a regex

    def virtual_host_paths(self):
        return {"available": "/etc/apache2/sites-available/"+self.name,
                  "enabled": "/etc/apache2/sites-enabled/"+self.name,
                     "link": "../sites-available/"+self.name}

    def virtual_host_contents(self):
        return "<VirtualHost *:80>\n    DocumentRoot /var/www/"+self.name+"/public\n    ServerName www."+self.domain+"\n    ServerAlias "+self.domain+"\n    RailsEnv development\n    RailsBaseURI /\n    PassengerPoolIdleTime 0\n    RailsFrameworkSpawnerIdleTime 0\n</VirtualHost>"

    def install_virtual_host(self):
        # Write the virtual host file
        virtual_host_file = open(self.virtual_host_paths()["available"], "w")
        virtual_host_file.write(self.virtual_host_contents())
        virtual_host_file.close()

        # Symbolically link it to "sites-enabled".  We'll use the "../" symbolic link instead of "/etc/apache2..." because that's what Ubuntu does.
        cwd_original = os.getcwd()

        os.chdir("/etc/apache2/sites-enabled/")
        os.symlink(self.virtual_host_paths()["link"], self.name)

        os.chdir(cwd_original)
        # Don't worry about restarting apache because we do a reboot later

    def install_rails_application(self):
        cwd_original = os.getcwd()

        os.chown("/var/www", 1000, 1000) # CHECK: It's probably not great to chown this to 1000:1000
        os.chdir("/var/www/")

        rails_arguments = ["sudo", "-u", "linode", "rails", "new", self.name, "-d", self.database]
        rails_process   = subprocess.call(rails_arguments)

        os.chdir(cwd_original)

    def install(self):
        self.install_virtual_host()
        self.install_rails_application()
        # cd /var/www && rails new... && chown...

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

        # Update rubygems
        # NOTE: We can't use "gem update --system" because it's disabled on Debian/Ubuntu so we have to use this workaround.
        rubygems_update = Gem("rubygems-update")
        rubygems_update.install()
   
        update_rubygems_arguments = ["/var/lib/gems/1.8/bin/update_rubygems"] # FIX: This will fail later when 1.8 is old
        update_rubygems_process   = subprocess.call(update_rubygems_arguments)

        # Install our gems
        self.setup_common(self.gems)

    def setup_files(self):
        # FIX: How will this handle tarballs?
        self.setup_common(self.files)

    def setup_websites(self):
        # Delete the "It Works!" page
        os.remove("/var/www/index.html")

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
        #print "upgrading:apt:packages"
        #self.cache.upgrade(True)

        for package in self.packages:
            package.install(self.cache)

        self.cache.commit()

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

