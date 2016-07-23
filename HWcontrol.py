# -*- coding: utf-8 -*-


#to kill python processes use  -- pkill python
import time
import datetime
import threading
#import sys,os
#import serial
import logging

global ISRPI

try:
	__import__("smbus")
except ImportError:
	ISRPI=False
else:
	import Adafruit_DHT #humidity temperature sensor
	import Adafruit_BMP.BMP085 as BMP085 #pressure sensor
	import spidev
	import smbus
	import RPi.GPIO as GPIO
	GPIO.setmode(GPIO.BCM) 
	ISRPI=True


HWCONTROLLIST=["tempsensor","humidsensor","pressuresensor","analogdigital","lightsensor","pulse","readpin","photo","mail+info+link","mail+info"]
RPIMODBGPIOPINLISTPLUS=["I2C", "SPI", "2", "3", "4","5","6", "7", "8", "9", "10", "11", "12","13","14", "15", "16","17", "18", "19", "20","21","22", "23", "24", "25","26", "27", "N/A"]
RPIMODBGPIOPINLIST=["2", "3", "4","5","6", "7", "8", "9", "10", "11", "12","13","14", "15", "16","17", "18", "19", "20","21","22", "23", "24", "25","26", "27","N/A"]
ADCCHANNELLIST=["0","1","2","3","4","5","6","7", "N/A"] #MCP3008 chip has 8 input channels

DHT22_data={'Temperature':None,'Humidity':None,'lastupdate':None}
DHT22_data['lastupdate']=datetime.datetime.now() - datetime.timedelta(seconds=2)

#" GPIO_data is an array of dictionary, total 40 items in the array
GPIO_data=[{"level":None, "state":None} for k in range(40)]


def execute_task(cmd, message, recdata):
	if cmd==HWCONTROLLIST[0]:
		return get_DHT22_temperature(cmd, message, recdata , DHT22_data)
		
	elif cmd==HWCONTROLLIST[1]:
		return get_DHT22_humidity(cmd, message, recdata , DHT22_data)

	elif cmd==HWCONTROLLIST[2]:
		return get_BMP180_pressure(cmd, message, recdata)

	elif cmd==HWCONTROLLIST[3]:
		retok=get_MCP3008_channel(cmd, message, recdata)
		return retok

	elif cmd==HWCONTROLLIST[4]:	
		return get_BH1750_light(cmd, message, recdata)

	elif cmd==HWCONTROLLIST[5]:	
		return gpio_pulse(cmd, message, recdata)

	elif cmd==HWCONTROLLIST[6]:	
		return gpio_pin_level(cmd, message, recdata)

	else:
		print "Command not found"
		recdata.append(cmd)
		recdata.append("e")
		recdata.append(0)
		return False;
	return False;


def execute_task_fake(cmd, message, recdata):
	
	if cmd==HWCONTROLLIST[0]:
		get_DHT22_temperature_fake(cmd, message, recdata, DHT22_data)
		return True;
	
	elif cmd==HWCONTROLLIST[5]:	
		gpio_pulse(cmd, message, recdata)
		return True;

	elif cmd==HWCONTROLLIST[6]:	
		gpio_pin_level(cmd, message, recdata)
		return True;
		
	else:
		print "no fake command available" , cmd
		recdata.append(cmd)
		recdata.append("e")
		recdata.append(0)
		return False;
	return True



def get_DHT22_temperature_fake(cmd, message, recdata, DHT22_data):
	deltat=datetime.datetime.now()-DHT22_data['lastupdate']
	if deltat.total_seconds()>2:
		
		DHT22_data['Humidity']="10.10"
		DHT22_data['Temperature']="20.10"
		DHT22_data['lastupdate']=datetime.datetime.now()

	recdata.append(cmd)
	recdata.append(DHT22_data['Temperature'])
	recdata.append(1)
	return DHT22_data['lastupdate']

def get_DHT22_temperature(cmd, message, recdata, DHT22_data):
	
	successflag=0
	msgarray=message.split(":")
	pin=int(msgarray[1])

	deltat=datetime.datetime.now()-DHT22_data['lastupdate']
	if deltat.total_seconds()>2:
		sensor = Adafruit_DHT.DHT22
		humidity, temperature = Adafruit_DHT.read(sensor, pin)

		if (humidity is not None) and (temperature is not None):
			print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
			DHT22_data['Humidity']=('{:3.2f}'.format(humidity / 1.))
			DHT22_data['Temperature']=('{:3.2f}'.format(temperature / 1.))
			DHT22_data['lastupdate']=datetime.datetime.now()
			successflag=1
		else:
			print 'Failed to get DHT22 reading'
	else:
		successflag=1 # use the data in memory, reading less than 2 sec ago
		
	recdata.append(cmd)
	recdata.append(DHT22_data['Temperature'])
	recdata.append(successflag)	
	return DHT22_data['lastupdate']
	

def get_DHT22_humidity(cmd, message, recdata, DHT22_data):
	successflag=0
	msgarray=message.split(":")
	pin=int(msgarray[1])
	deltat=datetime.datetime.now()-DHT22_data['lastupdate']
	if deltat.total_seconds()>2:
		sensor = Adafruit_DHT.DHT22
		humidity, temperature = Adafruit_DHT.read(sensor, pin)

		if (humidity is not None) and (temperature is not None):
			print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
			DHT22_data['Humidity']=('{:3.2f}'.format(humidity / 1.))
			DHT22_data['Temperature']=('{:3.2f}'.format(temperature / 1.))
			DHT22_data['lastupdate']=datetime.datetime.now()
			successflag=1
		else:
			print 'Failed to get DHT22 reading'
	else:
		successflag=1 # use the data in memory, reading less than 2 sec ago
		
	recdata.append(cmd)
	recdata.append(DHT22_data['Humidity'])
	recdata.append(successflag)	
	return DHT22_data['lastupdate']


def get_BMP180_pressure(cmd, message, recdata):
	successflag=0
	Pressure=0
	try:
		sensor = BMP085.BMP085(3) # 3 = High resolution mode
		Pressure = '{0:0.2f}'.format(sensor.read_pressure()/float(100))
		successflag=1
	except:
		print " I2C bus reading error, BMP180 , pressure sensor "
	#pressure is in hecto Pascal
	recdata.append(cmd)
	recdata.append(Pressure)
	recdata.append(successflag)	
	return True
	
	
def get_BH1750_light(cmd, message, recdata):
	successflag=0
	
	DEVICE     = 0x23 # Default device I2C address
	POWER_DOWN = 0x00 # No active state
	POWER_ON   = 0x01 # Power on
	RESET      = 0x07 # Reset data register value
	# Start measurement at 4lx resolution. Time typically 16ms.
	CONTINUOUS_LOW_RES_MODE = 0x13
	# Start measurement at 1lx resolution. Time typically 120ms
	CONTINUOUS_HIGH_RES_MODE_1 = 0x10
	# Start measurement at 0.5lx resolution. Time typically 120ms
	CONTINUOUS_HIGH_RES_MODE_2 = 0x11
	# Start measurement at 1lx resolution. Time typically 120ms
	# Device is automatically set to Power Down after measurement.
	ONE_TIME_HIGH_RES_MODE_1 = 0x20
	# Start measurement at 0.5lx resolution. Time typically 120ms
	# Device is automatically set to Power Down after measurement.
	ONE_TIME_HIGH_RES_MODE_2 = 0x21
	# Start measurement at 1lx resolution. Time typically 120ms
	# Device is automatically set to Power Down after measurement.
	ONE_TIME_LOW_RES_MODE = 0x23

	bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
	light=0
	try:
		data = bus.read_i2c_block_data(DEVICE,ONE_TIME_HIGH_RES_MODE_1)
		light = '{0:0.2f}'.format(((data[1] + (256 * data[0])) / 1.2))
		successflag=1  
	except:
		print " I2C bus reading error, BH1750 , light sensor "
	
	recdata.append(cmd)
	recdata.append(light)
	recdata.append(successflag)	
	return True
	
	
def get_MCP3008_channel(cmd, message, recdata):
	
	successflag=0
	volts=0
	
	msgarray=message.split(":")
	
	messagelen=len(msgarray)
	
	#PIN=msgarray[1]

	SUBPIN=int(msgarray[2])
	#if messagelen>3:	
	POWERPIN=int(msgarray[3])
	
	channel=SUBPIN
	
	#enable power on the hygrometer
	GPIO_setup(POWERPIN, "out")
	GPIO_output(POWERPIN, 1)
	time.sleep(0.2)
	
	try:
		# Open SPI bus
		spi = spidev.SpiDev()
		spi.open(0,0)

		# Function to read SPI data from MCP3008 chip
		# Channel must be an integer 0-7

		adc = spi.xfer2([1,(8+channel)<<4,0])
	
		data = ((adc[1]&3) << 8) + adc[2]

		# Function to convert data to voltage level,
		# rounded to specified number of decimal places.
		volts = (data * 3.3) / float(1023)
		volts = round(volts,2)

		spi.close()
		successflag=1
	except:
		print " I2C bus reading error, MCP3008 , AnalogDigitalConverter  "
	
	recdata.append(cmd)
	recdata.append(volts)
	recdata.append(successflag)	
	#set powerpin to zero again
	GPIO_output(POWERPIN, 0)

	return True	

def GPIO_output(PIN, level):
	if ISRPI:
		GPIO.output(PIN, level)
	GPIO_data[PIN]["level"]=level
	return True

def GPIO_setup(PIN, state):
	if ISRPI:
		if state=="out":
			GPIO.setup(PIN,  GPIO.OUT)
		else:
			GPIO.setup(PIN,  GPIO.IN)
	GPIO_data[PIN]["state"]=state
	return True

def endpulse(PIN,logic):

	if logic=="pos":
		level=0
	else:
		level=1
	GPIO_output(PIN, level)
	
	print "pulse ended", time.ctime() , " PIN=", PIN , " Logic=", logic , " Level=", level
	return True


def gpio_pulse(cmd, message, recdata):
	msgarray=message.split(":")
	PIN=int(msgarray[1])
	testpulsetime=msgarray[2]
	pulsesecond=int(testpulsetime)/1000
	
	if len(msgarray)>3:
		logic="neg"
	else:
		logic="pos"	
		
	GPIO_setup(PIN, "out")
	if logic=="pos":
		level=1
	else:
		level=0
	GPIO_output(PIN, level)
		
	t = threading.Timer(pulsesecond, endpulse, [PIN , logic]).start()
	print "pulse started", time.ctime() , " PIN=", PIN , " Logic=", logic , " Level=", level
	recdata.append(cmd)
	recdata.append(PIN)
	return True	

def gpio_pin_level(cmd, message, recdata):
	msgarray=message.split(":")
	PIN=int(msgarray[1])
	recdata.append(msgarray[0])
	if GPIO_data[PIN]["level"] is not None:
		recdata.append(str(GPIO_data[PIN]["level"]))
		return True
	else:
		recdata.append("e")
		return False	




def sendcommand(cmd, message, recdata):
	# as future upgrade this function might be run asincronously using "import threading"

	if ISRPI:
		ack=execute_task(cmd, message, recdata)
	else:
		ack=execute_task_fake(cmd, message, recdata)
	return ack
	






if __name__ == '__main__':
	
	"""
	to be acknowledge a message should include the command and a message to identyfy it "identifier" (example "temp"), 
	if arduino answer including the same identifier then the message is acknowledged (return true) command is "1"
	the data answer "recdata" is a vector. the [0] field is the identifier, from [1] start the received data
	"""
	recdata=[]
	for i in range(0,30):
		get_DHT22_temperature_fake("tempsensor1", "" , recdata , DHT22_data )
		time.sleep(0.4)
		print DHT22_data['lastupdate']
