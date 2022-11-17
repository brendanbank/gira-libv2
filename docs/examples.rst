Examples
============


These script expects the following environment variables to be set. You can create a .env file 
including the format below main directory where this script is run to load the environment variables.

.. highlight:: python
.. code-block:: python

	
	DEBUG=<True|False>
	HOSTNAME=<local LAN IP address of your X1>
	USERNAME=<username of the X1>
	PASSWORD=<password of the X1>
	SQLALCHEMY_DATABASE_URI=<database URI>
	GIRA_USERNAME=<username of the https://geraeteportal.gira.de/ portal>
	GIRA_PASSWORD=<pasword of the https://geraeteportal.gira.de/ portal>
	VPN_HOST=<url to your X1 link through the Gira S1>
	INSTANCE_NAME=<instance name, used for storing your key variables
	    (cookies, authorization keys) in your persistent cache>

The VPN_HOST has the following sturcture 

	https://http.httpaccess.net/[serviceId]/httpu://[local LAN ip address of your X1]
		
It can be found in your S1 configuration on https://geraeteportal.gira.de/

You can add these variables to the .env file in the root of your project, the load_dotenv command will read them.



Webserver
-------------

.. automodule:: webserver

enableCallback
--------------

.. automodule:: enableCallback


disableCallback
---------------

.. automodule:: disableCallback
