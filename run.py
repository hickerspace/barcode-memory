#!/usr/bin/python
# -*- coding: utf-8 -*-

from threads.display import MemoryDisplay
from threads.test import TestThread
from threads.ledstrip import LedStrip
import logging

def main():
	"Initializes logging and starts the threads."
	logging.basicConfig(filename='memory.log', level=logging.DEBUG,
		format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y.%m.%d %H:%M:%S")

	# create LED strip
	ledstrip = LedStrip()
	# create display
	display = MemoryDisplay(ledstrip, noReturn=True)

	# start them
	ledstrip.start()
	display.start()


if __name__ == '__main__':
	main()

