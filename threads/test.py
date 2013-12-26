#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, time, logging

class TestThread(threading.Thread):
	"Example thread showing how to interact with the display thread."
	def __init__(self):
		threading.Thread.__init__(self)
		self.displayThread = None
		self.ledstripThread = None

	def run(self):
		# check if we got a connection to display thread
		if not self.displayThread:
			logging.critical("No display thread provided.")
			raise Exception("No display thread provided.")

		self.displayThread.showImg("images/spiral.png")
		self.ledstripThread.sendRed(0)
		time.sleep(3)
		self.displayThread.showImg("images/color-circle.png")
		self.ledstripThread.sendYellow(0)
		time.sleep(3)
		logging.info("Player took %d seconds to finish." % self.displayThread.playTime)

		logging.info("New game started.")
		self.displayThread.newGame()
		self.displayThread.showImg("images/spiral.png")
		self.ledstripThread.sendGreen(0)

