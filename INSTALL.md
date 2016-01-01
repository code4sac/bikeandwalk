#Bike and Walk App
##Installation

We'll assume for this document that we will be installing
the app into it's own directory called `app.bikeandwalk.org`.

###Git the files:
In the terminal, cd into the directory one directory up from
where you want to install the app, type:

`$ git clone https://github.com/wleddy/bikeandwalk.git`

This will create a new direcory named `bikeandwalk`

Rename that directory to `app.bikeandwalk.org`:

`$ mv bikeandwalk app.bikeandwalk.org`

cd into the new direcorty:

`$ cd app.bikeandwalk.org`

###Install the virtualenv:
The virtualenv will contain the python installation for the app.

In the terminal create a virtual environment named `env`:

`app.bikeandwalk.org $ virtualenv --no-site-packages env`

If your version of python is different than the one used to compile 
your copy of `mod_wsgi` you will need to have virtualenv install the
corresponding version of python in the virtualenv. So, for python 2.6,
run this instead:

`app.bikeandwalk.org $ virtualenv --no-site-packages --python=python2.6 env`

###Activate your new virtualenv:
Activate your virtual environment from the terminal with:

`app.bikeandwalk.org $ . env/bin/activate`

Your terminal prompt will now be prefixed by "(env)" to indicate that you are using 
the environment.

###Load the python packages with pip
Load the dependencies with pip and the requirements.txt file:

`(env)app.bikeandwalk.org $ pip install -r requirements.txt`

###Run the setup script
Run the setup script to create your local configuration settings:

`(env)app.bikeandwalk.org $ python setup.py`

This will create two directories and three files.

1. A directory named `instance` containing a file named `settings.conf`
2. A directory named `apache` containing a file named `bikeandwalk.wsgi`
3. An empty file named `bikeandwalk.sqlite` which will serve as your datafile

You will use these files to set some of the configuration options for the app.

#####Settings.conf
At a minimum you will need to set the location for the database file by un-commenting
and changing the values for:

`DATABASE` may be set to another name if you like.

`DATABASE_PATH_PREFIX` must be set to the absolute path to the database file, but without 
the filename itself.

`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` and `SMTP_PASSWORD` need to be set to your mail server so
that you can send email invitation to your counters.

#####bikeandwalk.wsgi
`bikeandwalk.wsgi` is the file that apache web server will call for each web request.

You may need to change the `FULL_PATH_TO_YOUR_APP` to match your path.

###Set up Apache and mod_wsgi
In the main apache config file, enable the mod_wsgi extension with `LoadModule wsgi_module` and
the location of the .so file.

Next create a "virgin" virtualenv directory as described above but located somewhere other than
your app directory. The WSGI docs recommend something like:
`$ cd /usr/local/pythonenv`

`$ sudo virtualenv --no-site-packages BASELINE`

Back in the main apache config file, add:

`WSGIPythonHome /usr/local/pythonenv/BASELINE`

###Run the app
Run the app from the terminal to initialize the database and test the installation:

`(env)app.bikeandwalk.org $ python bikeandwalk.py`

You should see a message "Web Server Running". If you do, type control+c to stop the server or you
can test the app in your browser at `localhost:5000`.

To exit the virtual environment type:

`(env)app.bikeandwalk.org $ deactivate`


For more information on mod_wsgi, see the [WSGI Documentation](http://modwsgi.readthedocs.org/en/develop/installation.html)
