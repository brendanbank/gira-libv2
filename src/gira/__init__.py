'''

############################################################
Welcome to Gira lib v2's documentation!
############################################################

This is second version to the python library I created to interact with my X1/S1 Gira server. This library implements the 
full scope of the REST interface as described by the 
`Gira IoT REST API Documentation <https://github.com/brendanbank/gira-libv2/blob/c8993841cf787944a9087aa905c05484d40ae7cd/GiraDocumentation/Gira_IoT_REST_API_v2_EN.pdf>`__

A couple of features:

* Login through the S1 remote access functionality
* Download configuration and create a internal memory structure to get and set values on the X1.

**VPN Login:**


.. image:: https://raw.githubusercontent.com/brendanbank/gira-libv2/9b4ab1e3f3ed67b62e4f1ecf36bf35ff6a9d8ed9/GiraDocumentation/GIRA_VPN_Access.png
  :width: 900
  
 
#.  The module tries to login to https://geraeteportal.gira.de/ with your username and password.
#.  A cookie (from httpaccess.net) is returned for the the link VPN link provided that was requested in the previous step.
    You can see these links when you login to the geraeteportal.gira.de and go to you S1 device. Click on Links
    and you should find the links you can go visit through the S1. Find the link to the X1 device (it should be 
    pre-programed. If you crearte it).  Note that you have to select the link with the 'HTTPS without certificate check' 
    enabled. The X1 web server security certificate is signed by the 'Gira CA' Certificate Authority which is not
    trusted by most browsers.
    
    The link has the following structure.
    
        https://http.httpaccess.net/[serviceId]/**httpu:**//[local LAN ip address of your X1]
        
    Note the **'httpu'** if you link has 'http' (without the 'u') your application may not be able to login. As the
    httpaccess.net portal expects a ssl certificate were the Certificate Authority is known. 
#.  Now that you have a authentication Cookie from httpaccess.net you can use this cookie to connect to the vpn link.
    and login to your X1/Homeserver. This is done with the username of the device itself. Not with the credientials
    of the geraeteportal.gira.de portal.
#.  The X1 will return a authentication token that you can use for future logins.





'''

from gira.cache import CacheObject
from gira.device import GiraServer