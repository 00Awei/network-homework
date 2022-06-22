import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

#get the checksum of the packet
def checksum(str):
    csum = 0
    countTo = (len(str) / 2) * 2
    count = 0

    while count < countTo:
        thisVal = str[count + 1] * 256 + str[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(str):
        csum = csum + str[len(str) - 1].decode()
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

#receive the 'pong'
def receiveOnePing(mySocket, ID, sequence, destAddr, timeout):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  #Timeout
            return 0
        #calculate the delay time
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        #get the ICMP header from the IP packet
        header = recPacket[20: 28]
        type, code, checksum, packetID, sequence = struct.unpack("!bbHHh",header)
        if type == 0 and packetID == ID:
            byte_in_double = struct.calcsize("!d")
            timeSent = struct.unpack("!d", recPacket[28: 28 + byte_in_double])[0]
            delay = timeReceived - timeSent
            ttl = ord(struct.unpack("!c", recPacket[8: 9])[0].decode())
            return (delay, ttl, byte_in_double)

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None

#send request
def sendOnePing(mySocket, ID, sequence, destAddr):
    #Header is type(8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0     #Make a dummy header with a 0 checksum

    #struct is used to interpret str as packed binary data
    header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, sequence)
    data = struct.pack("!d", time.time())
    #calculate the checksum on the data and the dummy header
    myChecksum = checksum(header + data)

    #get the right checksum, and put it in the header
    header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, sequence)
    packet = header +data

    mySocket.sendto(packet, (destAddr, 1))

#execute the action of 'ping'
def doOnePing(destAddr, ID, sequence, timeout):
    icmp = socket.getprotobyname("icmp")
    #Create socket
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    sendOnePing(mySocket, ID, sequence, destAddr)
    delay = receiveOnePing(mySocket, ID, sequence, destAddr, timeout)

    mySocket.close()
    return delay

def ping(host, timeout=1):
    dest = socket.gethostbyname(host)
    print("Pinging " + dest + " using python:")
    print(" ")

    myID = os.getpid() & 0xFFFF
    loss = 0
    for i in range(4):
        result = doOnePing(dest, myID, i, timeout)
        if not result:
            print("Request time out")
            loss += 1
        else:
            delay = int(result[0]*1000)
            ttl = result[1]
            bytes = result[2]
            print("Received from " + dest + ": byte(s)=" + str(bytes) + " delay=" + str(delay) + "ms TTL=" + str(ttl))
            time.sleep(1)    #the time of timeout
    print("Packet:sent = " + str(4) + " received = " + str(4-loss) + " lost = " + str(loss))

    return

def main():
    c = input("continue?  y/n ")
    if c == "y":
        x = input("enter the url or ip address of the host that you want to ping:")
        ping(x)
        print("")
        return main()
    else:
        return None

main()