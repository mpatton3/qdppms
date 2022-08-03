# This script contains classes and functions for communicating with
# MultiVu over a socket server.


import time, socket, sys
from PythonControl.parse_inputs import inputs


def query_temp(host, port):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Query Temperature
    sock.sendall(b'temp?\r')

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.sendall(b'close\r')
    clrp = sock.recv(128).decode('utf-8')


    #print('second', reply)

    temp = float(reply[1])
    status = reply[-1].strip()

    #print('temp status', status)

    time.sleep(0.015)
    #print(temp, temp+1.2)

    return temp, status


def query_field(host, port):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Query Temperature
    sock.sendall(b'field?\r')

    #time.sleep(0.1)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8').split(',')

    #print('field query reply ', reply)
    # Disconnect from Socket Server
    sock.sendall(b'close\r')
    clrp = sock.recv(128).decode('utf-8')


    #print('second', reply)

    #print(reply)
    field = float(reply[1])
    status = reply[-1].strip()


    time.sleep(0.015)
    #print(temp, temp+1.2)

    return field, status


def set_temp(host, port, temp, rate):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    #time.sleep(0.5)
    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    #time.sleep(0.0)
    # Send Temperature Set command
    string = 'TEMP ' + str(temp) + ', ' + str(rate) + ', 0\r'
    print(string)
    sock.sendall(string.encode('utf-8'))

    reply = sock.recv(128).decode('utf-8')

    print('command send reply ', reply)


    #time.sleep(0.1)
    # Receive Temperature
    #reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.sendall(b'close\r')
    clrp = sock.recv(128).decode('utf-8')


    time.sleep(0.1)   # min wait time to not disconnect telnet port.

    #print('second', reply)

    #temp = float(reply[1])
    #print(temp, temp+1.2)

    #return temp


def set_field(host, port, field, rate):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)
    #time.sleep(0.1)
    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Send Field Set Command
    string = 'FIELD ' + str(field) + ', ' + str(rate) + ', 0, 1\r'
    print(string)
    sock.sendall(string.encode('utf-8'))

    reply = sock.recv(128).decode('utf-8')

    # Disconnect from Socket Server
    sock.sendall(b'close\r')
    clrp = sock.recv(128).decode('utf-8')

    time.sleep(0.1)   # min wait time to not disconnect telnet port.

    # Wait 1.8 seconds after setting this before asking if the field
    # is stable, b/c that is the PPMS cryostat response time to start
    # ramping the field.


def main():


    timeWas = time.time()
    #instrumentInfo = inputs(instrumentRequired=False)
    #instrument, simulateMode, host = instrumentInfo.parseInput(sys.argv[1:])
    host = "128.104.184.130"
    port = 5000
    #addr = (host, port)
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.connect(addr)
    #print(sock.recv(128).decode('utf-8'))



    print(query_temp(host, port))
    print(query_field(host, port))
    #print(query_temp(host, port))
    #print(query_field(host, port))
    #print(query_temp(host, port))
    #print(query_field(host, port))


    set_temp(host, port, 200.0, 13.5)
    #time.sleep(0.013)   # min wait time to not disconnect telnet port.
    #time.sleep(0.3)
    set_field(host, port, 4500.0, 100.0)
    #time.sleep(0.3)
    #set_temp(host, port, 300.0, 3.5)


    #time.sleep(0.48)

    print(query_temp(host, port))
    print(query_field(host, port))

    #sock.send(b'close\r')

    print('Elapsed Time', time.time() - timeWas)

if __name__ == '__main__':
    main()
