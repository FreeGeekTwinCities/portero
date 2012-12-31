Portero
=======
[Portero](http://github.com/freegeektwincities/portero) is a simplified ERP web interface for common tasks at [Free Geek Twin Cities](http://freegeektwincities.org).


Installation
------------
Portero is based on the [Flask](http://flask.pocoo.org/) web framework, and uses [openerp-client-lib](http://pypi.python.org/pypi/openerp-client-lib) to communicate with the OpenERP server, so to make it run:

1. Install Flask and related packages:

   > sudo apt-get install python-flask python-flaskext.wtf python-pip

   > sudo pip install openerp-client-lib Flask-Bootstrap

2. Download Portero (usually to e.g. /var/www/portero)

3. (Optional) Replace /etc/apache2/sites-available with apache-site file from portero

4. Copy portero_config.py.dist to portero_config.py and edit appropriately

