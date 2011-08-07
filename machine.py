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
# UTILITY->PYTHON --------------------------------
# ------------------------------------------------
def remove_file_if_exists(path):
    if os.path.isfile(path):
        os.remove(path)

def arguments_as_user(user, arguments):
    return ["sudo", "-i", "-u", user]+arguments

# ------------------------------------------------
# CLASS->USER ------------------------------------
# ------------------------------------------------
class User:
    def __init__(self, json):
        self.json           = json
        self.name           = json["name"]
        self.password       = json["password"]
        self.shell          = json["shell"]
        self.password_crypt = crypt.crypt(self.password, self.name) # CHECK: Is this salt what it's supposed to be (self.name)?

    def install(self):
        # Add the user
        useradd_arguments = ["useradd", "--create-home", "--password", self.password_crypt, self.name]
        useradd_process   = subprocess.call(useradd_arguments)

        # Add them to sudoers NOPASSWD
        # FIX: This should be an option
        sudoers_file_path = "/etc/sudoers.d/"+self.name
        sudoers_file = open(sudoers_file_path, "w")
        sudoers_file.write(self.name+" ALL=NOPASSWD: ALL")
        sudoers_file.close()
        
        os.chmod(sudoers_file_path, 0440)

        # Change their shell
        chsh_arguments = ["chsh", "--shell", "/bin/"+self.shell, self.name]
        chsh_process   = subprocess.call(chsh_arguments)

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

# ------------------------------------------------
# CLASS->DATABASE --------------------------------
# ------------------------------------------------
class Database:
    def __init__(self, owner, name):
        self.owner    = owner
        self.user     = owner
        self.password = owner
        self.name     = name

    def install(self):
        print "installing:database: \""+self.name+"\""

        createuser_arguments = arguments_as_user("postgres", ["createuser", "-DSR", "--no-password", self.user])
        createuser_process   = subprocess.call(createuser_arguments)

        createdb_arguments = arguments_as_user("postgres", ["createdb", "-O", self.user, self.name])
        createdb_process   = subprocess.call(createdb_arguments)

# ------------------------------------------------
# CLASS->GIT-REPOSITORY --------------------------
# ------------------------------------------------
class GitRepository:
    def __init__(self, json, git_user):
        self.json     = json
        self.url      = json["url"]
        self.path     = json["path"]
        self.git_user = git_user

    def install(self):
        print "install:git-repository"
        # FIX: This won't expand ~/ because the user we're running this under is "root" instead of our target user.
        git_arguments = arguments_as_user(self.git_user.user, ["git", "clone", "git://"+self.url, self.path])
        git_process   = subprocess.call(git_arguments)

# ------------------------------------------------
# CLASS->GIT-USER --------------------------------
# ------------------------------------------------
class GitUser:
    def __init__(self, json):
        self.json  = json
        self.user  = json["user"]
        self.name  = json["name"]
        self.email = json["email"]

        self.repositories = map(lambda json: GitRepository(json, self), self.json["repositories"])

    def install(self):
        print "installing:git-user: \""+self.name+"\""

        git_arguments = arguments_as_user(self.user, ["git", "config", "--global", "user.name", self.name])
        git_process   = subprocess.call(git_arguments)
        
        git_arguments = arguments_as_user(self.user, ["git", "config", "--global", "user.email", self.email])
        git_process   = subprocess.call(git_arguments)

        for repository in self.repositories:
            repository.install()

# ------------------------------------------------
# CLASS->WEBSITE ---------------------------------
# ------------------------------------------------
class Website:
    def __init__(self, json):
        # CHECK: Do we even need self.name? Should everything be based on the domain instead in case we have foo.com and foo.org which are different sites?
        self.json          = json
        self.domain        = json["domain"]
        self.database_type = json["database_type"]
        self.name          = json["name"] # FIX: Extract this with a regex

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
        if not os.path.isfile("/etc/apache2/sites-enabled/"+self.name):
            cwd_original = os.getcwd()
            os.chdir("/etc/apache2/sites-enabled/")
            os.symlink(self.virtual_host_paths()["link"], self.name)
            os.chdir(cwd_original)

    def install_rails_application(self):
        os.chown("/var/www", 1000, 1000) # FIX: It's probably not great to chown this to 1000:1000... this diregards any other non-privileged users besides the first one

        rails_arguments = arguments_as_user("linode", ["rails", "new", "/var/www/"+self.name, "-d", self.database_type]) # FIX: Hardcoded linode...
        rails_process   = subprocess.call(rails_arguments)

    def install_databases(self):
        for database_name in [self.name+"_development", self.name+"_production", self.name+"_test"]:
            database = Database(self.name, database_name)
            database.install()

    def install(self):
        self.install_virtual_host()
        self.install_rails_application()
        self.install_databases()

# ------------------------------------------------
# CLASS->MACHINE ---------------------------------
# ------------------------------------------------
class Machine:
    
    def __init__(self, path_json):
        self.json = open(path_json)
        self.json = json.load(self.json)

        self.packages  = map(lambda name: Package(name), self.json["packages"])
        self.gems      = map(lambda name:     Gem(name), self.json["gems"])
        self.files     = map(lambda json:    File(json), self.json["files"])
        self.websites  = map(lambda json: Website(json), self.json["websites"])
        self.users     = map(lambda json:    User(json), self.json["users"])
        self.git_users = map(lambda json: GitUser(json), self.json["git"])

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
        # Delete the "It works!" page
        remove_file_if_exists("/var/www/index.html")

        #for website in self.websites:
        #    website.database = Database(website.name)

        self.setup_common(self.websites)

    def setup_users(self):
        self.setup_common(self.users)

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

    def setup_git(self):
        self.setup_common(self.git_users)

        # TEMPORARY: Make these a hook in configs
        remove_file_if_exists("/home/linode/.zshrc")
        ln_arguments = arguments_as_user("linode", ["ln", "-s", "/home/linode/.configs/zshrc", "/home/linode/.zshrc"])
        ln_process   = subprocess.call(ln_arguments)

        ln_arguments = ["ln", "-s", "/home/linode/.configs/zshrc-shared", "/etc/zshrc-shared"]
        ln_process   = subprocess.call(ln_arguments)

    # --------------------------------------------
    # SETUP --------------------------------------
    # --------------------------------------------
    def setup(self):
        self.setup_users()
        self.setup_packages()
        self.setup_files()
        self.setup_gems()
        self.setup_websites()
        self.setup_git()
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

