import serial
import time


'''
************************************************************************************************************************************************************************

The following commands try to open the serial ports for the RV-2AJ and an Arduino powered gripper. If they get the serial.Excetpion they will give an error message.
They require the exact string to be put thought like 'start' + 'stop' and 'exit'. The commands are written in MoveMaster Command. We use a prefix before the commmands
called b'1:1:. This converts the ASCII text to bytes. The 1;1 are needed to identify which robot and controller on the network is being used. We always send 1;1 because
we only have one controller and one robot.

*************************************************************************************************************************************************************************
'''
        
class SciGrip:
    
    def __init__(self, com, baud):
        self.com = com
        self.baud = baud

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
        pass

    def send(self, bytes): # use this to create the send command for the rest of
        pass


'''
*************************************************************************************
The following code is used to generate position data and alter it to be fed back into
a move command sent to the robot. This is done by reading the values coming from the
controller using 'JPOSF' and saving those to a variable. The values are then modified
and put into a dictionary. The values can be adjusted by doing simple dictionary jaz
so that we can add/subtract intergers from positons. The final piece is to extrat the
values into a list called movePos that we can use to send move commands to the robot. 
*************************************************************************************
'''


class RV2AJ():
    
    def __init__():
        self.con = serial.Serial('COM7')
        if self.con.isOpen() == True:
            print('Robot is connected!.\n')
        
    def start(self):
        self.con.write(b'1;1;RSTALRM\r\r\n')
        self.con.write(b'1;1;CNTLON\r\r\n')
        self.con.write(b'1;1;SRVON\r\r\n')
        print ("Servos are ON")
        time.sleep(.2)

    def stop(self):
        self.con.write(b'1;1;SRVOFF\r')
        print ("Servos are OFF")
        time.sleep(.2)
        
    def pos():
        userInput = '1;1;JPOSF\r'
        userInput = userInput.encode()  # send the byte (encode) command to read the position feedback values from the controller
        ser.write(userInput)
        #time.sleep(.2)
        #store the value(s) read back in the pos.position variable. I had to use pos.position to get it out of the funcion. 
        pos.position = ser.readline()
        pos.position = pos.position.decode("utf-8")

    def moveTo(userInput):
        userInput = '1;1;EXECMVS ' + userInput + '\r'
        userInput = userInput.encode()
        #time.sleep(.5)
        ser.write(userInput)
        #time.sleep(.5)
        read()

    def moveRel(): 
        userInput = '1;1;EXECJCOSIROP = (' + movePos + ')\r'
        userInput = userInput.encode()
        ser.write(userInput)
        time.sleep(.2)
        ser.write(b'1;1;EXECMOV JCOSIROP\r')
        time.sleep(.3)
        #read()


    def updateJoint(joint,value,progRun):
        global movePos
        while progRun >= 1:
            posDic[joint] = str(float(posDic[joint])+ value)
            movePosGen()
            moveRel()
            time.sleep(.2)
            progRun -= 1
            


    def readSerial():
        pass


'''
*********************************************************************
TODO: The following code is supposed to allow the arm to update in
real time absed on the positions being fed into it. It is my way of
trying to get the robot to Jog. It doesn't seem to work at this time. 
*********************************************************************
    #here were run the pos() function all the time to get the position all the time. Probably not the best idea!
    pos()
    position = pos.position
    #the values come back from the controller seperated by the ';" symbol. We also trim off the QoK that the controller always sends back.
    position = position[3:].split(';')
    posDic = {}
    #delete the junk we don't need in the dictionary. This step IS NOT neecsarry but makes it easy to read. 
    for i in range(len(position)-1):
        posDic[position[i]] = position[i+1]
    delEntries = ('J4','****,****','0.00','20.00','****','')
    for key in delEntries:
        if key in posDic:
            del posDic[key]
            
    #create the positions matrix to send to the controller. Note we don't have a 'J4' (this is specifict the the RV-2AJ) and the last two parameters are speed and ????. 

    def movePosGen():
        global movePos
        movePosList = (posDic['J1'],posDic['J2'],posDic['J3'],'0.00',posDic['J5'],posDic['J6'])
        movePos = ','.join(movePosList)

'''







