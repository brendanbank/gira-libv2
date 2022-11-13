# gira-libv2

This is version to the python library I created to interact with my X1/S1 Gira server.

This library implements the full scope of the REST interface as described by the [GPA Project Interface Documentation](https://github.com/brendanbank/gira-libv2/blob/c8993841cf787944a9087aa905c05484d40ae7cd/GiraDocumentation/GPA_Project_Interface_Documentation.pdf)

A couple of features:
* Login through the S1 remote access functionality
* Download configuration and create a internal memory structure to get and set values on the X1.

## VPN Login


The VPN login functionality is using the feature of the S1 to connect to devices in the S1 network on the local LAN side.

You can find these links when you login to geraeteportal.gira.de and go to you S1 device. Click on Links and you should fine the link to the X1 device. Note that you have to select the link with the 'HTTPS without certificate check' enabled. The X1 web server security certificate is signed by the 'Gira CA' Certificate Authority which is not trusted by most browsers. 

The link has the following structure. 

	https://http.httpaccess.net/[serviceId]/httpu://[local LAN ip address of your X1]

Note the **'httpu'** if you link does **'http'** (without the 'u') your application may not be able to login.


![VPN Login](https://github.com/brendanbank/gira-libv2/blob/9b4ab1e3f3ed67b62e4f1ecf36bf35ff6a9d8ed9/GiraDocumentation/GIRA_VPN_Access.png)