## Initialize a new installation
import os
from shutil import copyfile
import sys

DEFAULT_SETTINGS = 'default_site_settings.txt'

def init_site_settings(force=False):
    #Create the local setings strucutre
    # create the instance directory if it does not exist
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(d):
        os.makedirs(d)
        print "Instance directory created"
        
    # get the sample settings
    s = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_SETTINGS)
    if os.path.exists(s):
        #create the settings.conf file there if it does not exist
        f = os.path.join(d, "settings.conf")
        if os.path.exists(f) and force:
            os.remove(f)
            print "Old settings file removed"
        if not os.path.exists(f):
            #copy the default settings
            copyfile(s,f)
            print "setting file created"
        else:
            print "Settings file already exists. use 'setup.py force' to replace existing file."
            
    else:
        print "Default settings file, '"+ DEFAULT_SETTINGS +"' could not be found"
          

DEFAULT_WSGI_FILE = 'default_wsgi_script.txt'

def init_apache_wsgi(force=False):
    #Create the apache wsgi script
    # create the apach directory if it does not exist
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apache')
    if not os.path.exists(d):
        os.makedirs(d)
        print('Apache directory created')
        
    # get the sample settings
    s = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_WSGI_FILE)
    if os.path.exists(s):
        #create the wsgi file there if it does not exist
        f = os.path.join(d, "bikeandwalk.wsgi")
        if os.path.exists(f) and force:
            os.remove(f)
            print "old wsgi file removed"
        if not os.path.exists(f):
            #copy the default settings
            copyfile(s,f)
            print "apache wsgi file created"
        else:
            print "WSGI file already exists. use 'setup.py force' to replace existing file."
    else:
        print "The default wsgi file, '"+ DEFAULT_WSGI_FILE +"' could not be found"
            
DEFAULT_SQLITE_FILE = 'bikeandwalk.sql'

def init_sqlite_file(force=False):
    #just create an empty file
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_SQLITE_FILE)
    if os.path.exists(f) and force:
        os.remove(f)
        print "old data file removed"
    if not os.path.exists(f):
        #copy the default settings
        open(f,"a").close()
        print "empty database file created"
    else:
        print "Database file already exists. use 'setup.py force' to replace existing file."
           
            
if __name__ == '__main__':
    force = False
    if len(sys.argv) > 1:
        force = (sys.argv[1] == "force")
    init_site_settings(force)
    init_apache_wsgi(force)
    init_sqlite_file(force)
