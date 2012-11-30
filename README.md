Portero
=======
[Portero](http://github.com/freegeektwincities/portero) is a simplified [Tryton](http://tryton.org) web interface for common tasks at [Free Geek Twin Cities](http://freegeektwincities.org).


Installation
------------
Portero is designed to be installed on the same server as Tryton, so you'll need to [install Tryton](http://doc.tryton.org/2.6/trytond/doc/topics/install.html) (and its client library, [Proteus](http://pypi.python.org/pypi/proteus))first - for Ubuntu machines, we have [a script](https://raw.github.com/FreeGeekTwinCities/fgtc-erp-scripts/master/tryton-2.6-installer.sh) that will help you install Tryton along with some supporting libraries.

Once Tryton's up and running, you'll need to have [Flask](http://flask.pocoo.org/) and a couple of additional packages ([Flask-WTF](http://pypi.python.org/pypi/Flask-WTF) for dealing with forms, and [Flask-Bootstrap](http://pypi.python.org/pypi/Flask-Bootstrap) 'cause Brian's not too CSS-savvy) - these can be installed by running:
	pip install 'Flask Flask-WTF Flask-Bootstrap'
