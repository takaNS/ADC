#! /usr/bin/python3

from ast import Try
import sys
import serial

try:
	S = serial.Serial(sys.argv[1],115200)
except (IndexError,serial.serialutil.SerialException):
	print("Please Choose Serial Port")
	print("List Serial Ports\r\n")
	print("Serial Port : device")
	import serial.tools.list_ports
	for p in list(serial.tools.list_ports.comports()):
		print(p.device , " : " , p.description)
	sys.exit(127)

import datetime as dt
import numpy as np
import os
import asyncio
import time

async def func():
	i = 0
	while True :
		print("logging now...",['-','\\','|','/'][i % 4],'\r\nPress [Ctrl + c] to stop\r',end = "\033[1A",)
		i += 1
		try :
			time.sleep(0.5)
		except KeyboardInterrupt:
			print('\n\n\nstop logging')
			sys.exit(0)
			
while True:
	# buf = [[0] * 5 for i in range(10000)]
	buf = np.empty((10000,5),dtype=object)
	cnt = 0
	now = dt.datetime.now()
	dir = now.strftime('./DATA/%Y/%m-%d')
	file = now.strftime(dir + '/%m-%d_%H-%M.log')

	asyncio.get_event_loop().run_until_complete(func())

	while (now + dt.timedelta(minutes=1)).minute != dt.datetime.now().minute:
		while True:
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

