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

1. Download source tarball from http://v6.openerp.com/downloads
1. Untar and change directory into it.
1. (optional) Setup a virtualenv.
1. ```pip install simplejson reportlab mako werkzeug babel python-dateutil python-openid PIL```
1. Manually install PyChart: ```wget https://launchpad.net/ubuntu/natty/+source/python-pychart/1.39-7/+files/python-pychart_1.39.orig.tar.gz; tar -zxvf python-pychart_1.39.orig.tar.gz; cd PyChart-1.39; python setup.py install; cd ..;```
1. run server: ```./openerp-server```

### Install Potero

1. (optional) Setup a virtualenv.
2. ```pip install -r requirements.txt

