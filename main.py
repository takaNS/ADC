#! /usr/bin/python3

import datetime as dt
import numpy as np
import serial
import sys
import os

try:
	SerialPort = sys.argv[1]
except IndexError:
	print("Please Choose Serial Port")
	print("List Serial Ports\r\n")
	print("Serial Port : device")
	import serial.tools.list_ports
	for p in list(serial.tools.list_ports.comports()):
		print(p.device , " : " , p.description)
	sys.exit(127)

S = serial.Serial(SerialPort,115200)

while True:
	# buf = [[0] * 5 for i in range(10000)]
	buf = np.empty((10000,5),dtype=object)
	cnt = 0
	now = dt.datetime.now()
	dir = now.strftime('./DATA/%Y/%m-%d')
	file = now.strftime(dir + '/%m-%d_%H-%M.log')

	while (now + dt.timedelta(minutes=1)).minute != dt.datetime.now().minute:
		buf[cnt][0] = dt.datetime.now().strftime('%F_%H:%M:%S.%f')
		try:
			buf[cnt][1:] = S.readline().decode().split()
		except ValueError:
			# print('ValueError')
			continue

		print(buf[cnt])
		cnt = cnt + 1

	os.makedirs(dir, exist_ok=True)
	np.savetxt(file, buf[:cnt-1], fmt="%s")