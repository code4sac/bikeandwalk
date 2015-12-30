## Initialize a new installation
import os
from shutil import copyfile

def init_site_settings(force=False):
    #Create the local setings strucutre
    # create the instance directory if it does not exist
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(d):
        os.makedirs(d)
    
    # get the sample settings
    s = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default_site_settings.txt')
    if os.path.exists(s):
        #create the settings.conf file there if it does not exist
        f = os.path.join(d, 'settings.conf')
        if os.path.exists(f) and force:
            os.remove(f)
        if not os.path.exists(f):
            #copy the default settings
            copyfile(s,f)
    
if __name__ == '__main__':
    init_site_settings(True)
    print "setting file created"