Portero
=======
[Portero](http://github.com/freegeektwincities/portero) is a simplified ERP web interface for common tasks at [Free Geek Twin Cities](http://freegeektwincities.org).


Installation
------------
Portero is based on the [Flask](http://flask.pocoo.org/) web framework, and uses [openerp-client-lib](http://pypi.python.org/pypi/openerp-client-lib) to communicate with the [OpenERP](http://doc.openerp.com) server, so to make it run:

1. Install Flask and related packages:

   > sudo apt-get install python-flask python-flaskext.wtf python-pip

   > sudo pip install openerp-client-lib Flask-Bootstrap

2. Download Portero (usually to e.g. /var/www/portero)

3. (Optional) Replace /etc/apache2/sites-available with apache-site file from portero

4. Copy portero_config.py.dist to portero_config.py and edit appropriately


Local Development
-----------------

### Install OpenERP Server on Mac

#### Setup database

1. Install Postgres (via homebrew).
1. OpenERP will not run as the default postgres user as it is very opinionated and thinks this is insecure (which for production it would be).
1. Create new user (```openerp```): ```createuser --createdb --username postgres --no-createrole --pwprompt openerp```
1. Enter the password and make a superuser when prompted.
1. Create new database: ```openerp```

#### Install server

1. Download source tarball from http://nightly.openerp.com/7.0/nightly/src/.  ```wget http://nightly.openerp.com/7.0/nightly/src/openerp-7.0-latest.tar.gz```
1. Untar and change directory into it.  ```tar -zxvf openerp-7.0-latest.tar.gz```
1. (optional) Setup a virtualenv.  If you do not use a virtualenv, you will probably have to ```sudo pip install``` things.
1. ```pip install simplejson reportlab mako werkzeug babel python-dateutil python-openid PIL unittest2 mock docutils jinja2 gdata```
1. Manually install PyChart: ```wget https://launchpad.net/ubuntu/natty/+source/python-pychart/1.39-7/+files/python-pychart_1.39.orig.tar.gz; tar -zxvf python-pychart_1.39.orig.tar.gz; cd PyChart-1.39; python setup.py install; cd ..;```

#### Configure Server

1. Create a ```openerp-server.conf``` file.
1. Update database password and other values if needed

    [options]
    admin_passwd = admin
    db_host = localhost
    db_port = False
    db_name = openerp
    db_user = openerp
    db_password = openerp

#### Run OpenERP server

1. Run server: ```./openerp-server --config=openerp-server.conf```.  The first time this is run, it will install all the needed tables in the database.  You can use the flag ```---without-demo``` to start fresh.
1. Go to http://localhost:8069/
1. Login with user: ```admin``` and password ```admin``` (or if changed in conf).
1. In the web interface, under Installed Modules, install the Timesheets module (will also install the Accounting module).

### Install Potero

1. (optional) Setup a virtualenv.
1. ```pip install -r requirements.txt```
1. Create and edit config: ```cp portero_config.py.dist portero_config.py```
1. Go to http://127.0.0.1:5000/

