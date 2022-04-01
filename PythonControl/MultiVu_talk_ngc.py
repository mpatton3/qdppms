# This script contains classes and functions for communicating with
# MultiVu over a socket server.


import time, socket, sys
from parse_inputs import inputs


def query_temp(host, port):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Query Temperature
    sock.send(b'temp?\r')

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.send(b'close\r')

    #print('second', reply)

    temp = float(reply[1])

    time.sleep(0.013)
    #print(temp, temp+1.2)

    return temp

def query_field(host, port):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Query Temperature
    sock.send(b'field?\r')

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.send(b'close\r')

    #print('second', reply)

    field = float(reply[1])

    time.sleep(0.013)
    #print(temp, temp+1.2)

    return field


def set_temp(host, port, temp, rate):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Send Temperature Set command
    string = 'TEMP ' + str(temp) + ', ' + str(rate) + ', 0\r'
    #print(string)
    sock.send(string.encode('utf-8'))

    # Receive Temperature
    #reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.send(b'close\r')

    time.sleep(0.013)   # min wait time to not disconnect telnet port.

    #print('second', reply)

    #temp = float(reply[1])
    #print(temp, temp+1.2)

    #return temp


def set_field(host, port, field, rate):

    # Connect to Socket Server
    addr = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    # Receive Temperature
    reply = sock.recv(128).decode('utf-8')
    #print('first', reply)

    # Send Field Set Command
    string = 'field ' + str(field) + ', ' + str(rate) + ', 0, 1\r'
    sock.send(string.encode('utf-8'))

    # Receive Temperature
    #reply = sock.recv(128).decode('utf-8').split(',')

    # Disconnect from Socket Server
    sock.send(b'close\r')

    time.sleep(0.013)   # min wait time to not disconnect telnet port.

    #print('second', reply)

    #temp = float(reply[1])
    #print(temp, temp+1.2)

    #return temp





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

    set_temp(host, port, 298.3, 1.5)
    #time.sleep(0.013)   # min wait time to not disconnect telnet port.
    set_field(host, port, 000.2, 200.1)


    #sock.send(b'close\r')

    print('Elapsed Time', time.time() - timeWas)

if __name__ == '__main__':
    main()
