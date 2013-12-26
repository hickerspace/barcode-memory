#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, time, logging, serial
from Queue import Queue, Empty
import random

class LedData:
	"Representation of a specific LED (no) and its color."
	def __init__(self, no, r, g, b):
		self.no = no
		self.r = r
		self.g = g
		self.b = b

class LedStrip(threading.Thread):
	"Thread controlling LED strip."
	def __init__(self):
		threading.Thread.__init__(self)
		self.q = Queue()
		self.leds = []
		self.animate = False
		self.ser = None
		self.serialInit()

	def serialInit(self, wait=True):
		try:
			self.ser = serial.Serial('/dev/ttyACM1', 9600)
			self.stopThread = False
			# the arduino seems to take quite long to be ready, so sleep
			if wait:
				time.sleep(1.5)
		except Exception:
			logging.exception("Could not locate Arduino. No serial connection found.")
			self.stopThread = True

	def run(self):
		while not self.stopThread:
			try:
				if self.animate and self.q.qsize() == 0:
					r = random.randint(0, 80)
					g = random.randint(0, 80)
					b = random.randint(0, 80)

					for i in range(0, len(self.leds)):
						if self.stopThread or not self.animate: break
						# send to LED strip via serial connection
						self.ser.write(chr(self.leds[i])+chr(r)+chr(g)+chr(b))
						time.sleep(0.5)

				else:
					ledData = self.q.get(True, 1)
					# send to LED strip via serial connection
					self.ser.write(chr(ledData.no)+chr(ledData.r)+chr(ledData.g)+chr(ledData.b))
					# delay to give the arduino time to process
					time.sleep(0.01)
			except Empty:
				pass
			except serial.SerialException:
				break

		logging.info("LED strip thread closed.")

	def close(self):
		self.stopThread = True
		if self.ser:
			self.ser.close()
			# reestablish connection to turn all LEDs off
			self.serialInit(False)
			self.ser.close()
		self.stopThread = True

	def sendColor(self, ledNo, r, g, b):
		"Takes a serial connection and sets a color to LED."
		self.animate = False
		if not -1 < ledNo < 50:
			logging.error("LED number not in range.")
		elif not (-1 < r < 256 or -1 < g < 256 or -1 < b < 256):
			logging.error("RGB value(s) not in range.")
		else:
			self.q.put(LedData(ledNo, r, g, b))

	def animation(self, leds):
		self.leds = sorted(leds)
		self.animate = True

	# some predefined color setters
	def sendYellow(self, ledNo):
		self.sendColor(ledNo, 70, 30, 0)

	def sendRed(self, ledNo):
		self.sendColor(ledNo, 90, 0, 0)

	def sendGreen(self, ledNo):
		self.sendColor(ledNo, 0, 90, 0)

	def sendBlue(self, ledNo):
		self.sendColor(ledNo, 0, 0, 90)

