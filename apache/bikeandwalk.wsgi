##  WSGI Setup ##

#####################################
# Notes on the apache setup:
# a directive like this must be in the MAIN http.confg file...
# WSGIPythonHome /Users/bleddy/Sites/bikeandwalk.org/app/env
# 
# Create a virgin virualenv with
# virtualenv --no-site-packages --python=python2.6 env
# (my version of mod_wsgi was built for python 2.6 so need match in virtualenv)
# 
# My https-vhosts contains this:
# 
# <VirtualHost *:80>
#     ServerName localhost
#     DocumentRoot "/Users/bleddy/Sites/bikeandwalk.org/app"
#     # user should be non-priveliged, not a suder
#     WSGIDaemonProcess bikeandwalk user=bleddy group=staff threads=5
#     WSGIScriptAlias / /Users/bleddy/Sites/bikeandwalk.org/app/apache/bikeandwalk.wsgi
#     
#     ## a directive like this must be in the MAIN http.confg file...
#     ## WSGIPythonHome /Users/bleddy/Sites/bikeandwalk.org/app/venv
#     
#     <Directory /Users/bleddy/Sites/bikeandwalk.org/app>
#         WSGIProcessGroup bikeandwalk
#         WSGIApplicationGroup %{GLOBAL}
#         Order deny,allow
#         Allow from all
#     </Directory>
#     
#     # Add static directory aliases
# 
# 
#     CustomLog "/Library/Logs/Apache2/localhost.access_log" common
#     ErrorLog "/Library/Logs/Apache2/localhost.com.error_log"
# </VirtualHost>
#########################################################


import sys
## put the app into the python path
sys.path.insert(0, '/Users/bleddy/Sites/bikeandwalk.org/app')

from bikeandwalk import app as application

