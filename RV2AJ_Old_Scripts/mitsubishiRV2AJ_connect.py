import serial
import time
import re

'''
************************************************************************************************************************************************************************

The following commands try to open the serial ports for the RV-2AJ and an Arduino powered gripper. If they get the serial.Excetpion they will give an error message.
Thtey require the exact string to be put thought like 'start' + 'stop' and 'exit'. The commands are written in MoveMaster Command. We use a prefix before the commmands
called b'1:1:. This converts the ASCII text to bytes. The 1;1 are needed to identify which robot and controller on the network is being used. We always send 1;1 because
we only have one controller and one robot.

*************************************************************************************************************************************************************************
'''


try:
    ser = serial.Serial(
        port = 'COM5',
        baudrate = 9600,
        parity = serial.PARITY_EVEN,
        stopbits = serial.STOPBITS_TWO,
        bytesize = serial.EIGHTBITS,
        timeout = 1
        )
    time.sleep(.5)
    if ser.isOpen() == True:
        print('Robot is connected!.\n')
        
except serial.SerialException:
    time.sleep(.5)
    print('Robot port not available or Robot controller not connected.\n')
    exit()
    
try:
    ser2 = serial.Serial(
        port = 'COM6',
        baudrate = 9600,
        parity = serial.PARITY_EVEN,
        stopbits = serial.STOPBITS_TWO,
        bytesize = serial.EIGHTBITS,
        timeout = .2
        )
    time.sleep(.5)
    if ser2.isOpen() == True: 
        print('Gripper is connected!.\n')
    
except serial.SerialException:
    time.sleep(.5)
    print('Gripper port not available or not connected.\n')


print ('''************************************
Type "start" to turn the servos on.
\r
Type "stop" to turn the servos off.
\r
Type "exit" to leave the application.
*************************************
\r
Enter your commands below.

''')

stripChar = 'b/r'

userInput = ''
out = []


def read():
    while True:
        out = ser.readline()
        out = out.decode("utf-8")
        print ("Serial Return = " + out)
        break
    

while ser.isOpen() == True:

    # get keyboard input
    userInput = input(">> ")

    if userInput == 'read':
        read()
  
    if userInput == 'exit':
        print ("Quitting...")
        time.sleep(.2)
        ser.close()
        print ("Closing serial...")
        time.sleep(.2)
        exit()
        
    if userInput == 'start':
        print("Starting robot....\n")
        time.sleep(.2)
        out = ser.read(10)
        out = out.decode("utf-8")
        ser.write(b'1;1;RSTALRM\r\r\n')
        print ('Resetting alarm...')
        read()
        ser.write(b'1;1;CNTLON\r\r\n')
        print ('Turning on controller...')
        read()
        time.sleep(.5)
        ser.write(b'1;1;SRVON\r\r\n')
        print ('Turning on motors...')
        read()
        print(out)

        
        
        
    if userInput == 'stop':
        time.sleep(0.5)
        ser.write(b'1;1;SRVOFF\r\r\n')
        print ("Robot is stopping")
        time.sleep(.2)
        read()

            
    if userInput == 'open':
        ser2.write(b'1\r\n')
        time.sleep(1)
        read()
            
    if userInput == 'close':
        ser2.write(b'2\r\n')
        time.sleep(1)
        read()
            
    if userInput not in ['start','stop','open','close']:
        userInput = '1;1;' + userInput + '\r\r\n'
        userInput = userInput.encode()
        time.sleep(.5)
        ser.write(userInput)
        time.sleep(.5)
        read()

