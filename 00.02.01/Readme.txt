Readme for Quantum Design Socket Server

#### Introduction ####
This server provides access to the set and get methods for temperature, field, and chamber on four QD platforms:
PPMS, DynaCool, VersaLab, MPMS3, and OptiCool. The server is implemented in Python, and runs on the same computer
as MultiVu. Clients connect to the server using sockets. Socket connections can be made from telnet or programs 
you write and can be implemented in many operating systems.

This is a very simple server, intended for expert use. The Python source is included, so feel free to modify it
to suit your needs.

The server interacts with MultiVu through its OLE interface--see the file qdinstrument.py. With knowledge of 
MultiVu's OLE methods you can add more capability. Also, you can uses qdinstrument.py to send commands to MultiVu from Python directly.

#### Getting Started ####
To get started, install a Python 3 distribution. Quantum Design recommends Anaconda (https://www.anaconda.com/products/individual)
because it includes everything needed for this server and other packages useful for scientific computing.  This code was built and tested using Python 3.7.  It is necessary to have the following modules installed:
    pythoncom
    win32com
which can both be installed using an Anaconda Powershell Prompt and typing
	$: conda install -c anaconda pywin32
	or
	pip install pywin32

In addition, install:
    msvcrt

Before starting the server, be sure that MultiVu is running. For testing purposes, you can use MultiVu in 
simulation mode on an office computer.

To start the server, go to a command prompt or use the Anaconda Powershell Prompt, and type:
    $: python qd_socket_server.py <platform> -ip="IPv4 address"
Be sure that python points to a python version 3 or higher.  If you are not sure which version of Python 
you are using, from a command prompt type:
    $: python --version
There are optional flags that can be called when starting the server.  As shown above, one flag is -ip="IPv4 address".  Using this flag is necessary if the server and client are going to be running on two different computers.  If they are on the same computer, then the -ip flag can be omitted and server will use 'localhost.'  To determine the server computer's IP address, type ipconfig at a command shell prompt and look for the IPv4 address.

Another useful flag is -h, which brings up help information:
    $: python qd_socket_server.py -h


To connect to the server from a client machine, telnet to the ip address of the server computer on port
5000. You will get the response "Connected to QDInstrument socket server." You can then type commands and 
verify that communication with MultiVu is working. A simple example is:
    TEMP?
This returns a line of comma-separated values of the form:
    "<command>", value, units, status
For example, if the command was TEMP?, the return may be
    "TEMP?", 296.000,"K","Stable"


#### Command List ####
In the following command list, commands are shown in all caps, but the server is case-independent. Argument 
and return numerical values are shown in lower case. One or more spaces must be inserted between the command and 
arguments. Arguments are comma-separated with or without spaces. The return codes can generally be ignored, 
but may be useful for troubleshooting. Below each command is the response. For a listing of status and state 
codes, see the section "Quantum Design MultiVu OLE Methods" in application node 1070-209.

TEMP?
"TEMP?", temperature, "K", status

TEMP temperature_setpoint, rate, mode
return_code
		note:  mode = 0: Fast Settle, 1: No Overshoot

FIELD?
"FIELD?", field, "Oe", status

FIELD field_setpoint, rate, approach_mode, field_mode
return_code
		note:  approach_mode = 0: Linear, 1: No Overshoot, 2: Oscillate
			   field_mode = 0: Persistent (PPMS and MPMS3 only), 1: Driven

CHAMBER?
"CHAMBER?",,, state

CHAMBER code
return_code
		note:  code = 0: Seal, 1: Purge/Seal, 2: Vent/Seal, 3: Pump continuous, 4: Vent continuous, 5: High vacuum

The following commands do not interact with MultiVu, but are for the server:
CLOSE   This closes the socket connection, leaving the server running (other programs can still connect).
EXIT    This causes the server to exit. No further connections are possible without restarting the server.

#### Testing the Server Using Scaffolding ####
For testing the server, QD has supplied a file called qd_socket_client.py.  This simulates a series of
queries for the temperature, field, and chamber status.  When complete, it displays the total time for
the queries. To run this, first start the server in scaffolding mode by using the -s flag:
    $: python qd_socket_server.py PPMS -s
Next, type the following at the command line:
    $: python qd_socket_client.py
This can be run on a separate computer from the one running the server, and the IP address of the server
can be specified by using the -ip="IPv4" flag.

#### Troubleshooting ####
Typical connection issues are due to:
- Firewall. You might need to allow connections on port 5000 in your firewall.
- Port conflict. If port 5000 is in use, open the file qd_socket_server.py and change the PORT value one with
no conflict.
