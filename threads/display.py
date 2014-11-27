#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygame, pygame.event, pygame.mouse
from datetime import timedelta
import os, threading, logging
from memory import Memory
import time

DEBUG = True

class MemoryDisplay(threading.Thread):
	"Displays timer and memory images. Handles barcode input (barcode scanner is a HID)."

	# taken from http://learn.adafruit.com/pi-video-output-using-pygame/pygame-drawing-functions
	def __init__(self, ledstrip, noReturn=False):
		"Ininitializes a new pygame screen using the framebuffer"
		threading.Thread.__init__(self)

		if DEBUG:
			logging.info("DEBUG MODE")
			self.screen = pygame.display.set_mode((640, 480))
		else:
			# Based on "Python GUI in Linux frame buffer"
			# http://www.karoltomala.com/blog/?p=679
			dispNo = os.getenv("DISPLAY")
			if dispNo:
				logging.info("I'm running under X display = %s" % dispNo)

			# Check which frame buffer drivers are available
			# Start with fbcon since directfb hangs with composite output
			drivers = ["fbcon", "directfb", "svgalib"]
			found = False
			for driver in drivers:
				# Make sure that SDL_VIDEODRIVER is set
				if not os.getenv("SDL_VIDEODRIVER"):
					os.putenv("SDL_VIDEODRIVER", driver)
				try:
					pygame.display.init()
				except pygame.error:
					logging.warning("Driver: %s failed." % driver)
					continue
				found = True
				break

			if not found:
				logging.critical("No suitable video driver found! Are you root?")
				raise Exception("No suitable video driver found! Are you root?")

			size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
			logging.info("Framebuffer size: %d x %d" % (size[0], size[1]))
			self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

		self.clock = pygame.time.Clock()
		self.playTime = 0
		# TODO: increase this to ~ 10 min (= 600)
		self.maxPlayTime = 600
		self.noReturn = noReturn
		self.barcode = ""
		self.runGame = True
		self.inGame = False
		self.lastImg = None

		self.ledstrip = ledstrip
		self.memory = Memory(self)

		# Clear the screen to start
		self.screen.fill((0, 0, 0))
		# Initialise font support
		pygame.font.init()
		# hide mouse pointer
		pygame.mouse.set_visible(False)
		# Render the screen
		pygame.display.update()

	def __del__(self):
		"Destructor to make sure pygame shuts down, etc."

	def scalePercentage(self, surface, perc):
		screenRect = self.screen.get_rect()
		surface = pygame.transform.scale(surface, (int(perc*screenRect.width),
			int(perc*screenRect.height)))
		return surface

	def showImg(self, img, firstMove):
		"Takes image path and displays the image."
		if not self.inGame: return
		self.screen.fill((0, 0, 0))
		mainImg = pygame.image.load(img).convert()
		mainImg = self.scalePercentage(mainImg, 1)
		self.screen.blit(mainImg, (0, 25))

		if firstMove:
			self.lastImg = img
		else:
			#pass
			secondary = pygame.image.load(self.lastImg).convert()
			secondary = self.scalePercentage(secondary, 0.25)
			self.screen.blit(secondary, (self.screen.get_rect().width-secondary.get_rect().width, 25))

		pygame.display.update()

	def newGame(self):
		"Resets the timer and clears the screen."
		self.inGame = True
		self.playTime = 0
		# clear incomplete barcodes
		self.barcode = ""
		# clear the screen to start
		self.screen.fill((0, 0, 0))
		# instructions
		font = pygame.font.Font(None, 35)
		instruction = font.render("Start scanning!", True, (255, 255, 255), (0, 0, 0))
		self.blitCenterX(instruction, 100)

	def endGame(self):
		self.inGame = False

	def handleKey(self):
		"Handles keyboard input: barcodes, RETURN and ESCAPE"
		events = pygame.event.get()
		for event in events:
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					# input complete
					logging.info("Barcode %s received." % self.barcode)
					self.memory.scan(self.barcode)
					self.barcode = ""
				elif event.key == pygame.K_ESCAPE:
					# exit
					logging.info("Exitting.. (Escape pressed)")
					self.close()
				elif event.key <= 127:
					self.barcode += chr(event.key)
					# if barcode scanner does not send return after barcode
					defaultLength = len(self.memory.barcodes[0])
					if self.noReturn and len(self.barcode) == defaultLength:
						returnEvent = pygame.event.Event(pygame.KEYDOWN,
							key=pygame.K_RETURN)
						pygame.event.post(returnEvent)

	def close(self):
		self.runGame = False
		# stop other threads
		self.ledstrip.close()

	def blitCenterX(self, surface, y):
		pos = surface.get_rect()
		pos.centerx = self.screen.get_rect().centerx
		pos.y = y
		self.screen.blit(surface, pos)

	def highscore(self, blink):

		self.ledstrip.animation(self.memory.barcodepositions.values())

		white = (255, 255, 255)
		black = (0, 0, 0)
		red = (255, 0, 0)
		green = (0, 255, 0)
		# clear screen
		self.screen.fill(black)
		titleFont = pygame.font.Font(None, 60)
		titleSurface = titleFont.render("Barcode Memory", True, white, black)
		self.blitCenterX(titleSurface, 0)

		font = pygame.font.Font(None, 35)

		if self.playTime > 0 and self.playTime <= self.maxPlayTime:
		 	time_ = str(timedelta(seconds=self.playTime))[2:]
			personal = font.render("Congratulations, your score: %s" % time_, True, red, black)
			self.blitCenterX(personal, 45)

		pos = 80
		for score in self.memory.loadHighscore()[:5]:
			delta, playTime = score
			scoreline = font.render("%s      %s" % (str(delta)[2:], playTime.strftime("%Y-%m-%d %H:%M")), True, white, black)
			self.blitCenterX(scoreline, pos)
			pos += 25

		if not blink:
			normal = font.render("Scan START to play!", True, green, black)
			self.blitCenterX(normal, 210)

		pygame.display.update()

	def run(self):
		# initialize font
		font = pygame.font.Font(None, 40)
		count = 0
		while self.runGame:
			if self.playTime > self.maxPlayTime:
				self.endGame()

			if self.inGame:
				# show timer
				timerSurface = font.render("Timer: %s" % str(timedelta(seconds=self.playTime))[2:],
					True, (255, 255, 255), (0, 0, 0))

				# blit text
				self.screen.blit(timerSurface, (0, 0))

				if count % 10 == 0:
					self.playTime += 1
			else:
				self.highscore(count < 3)

			if count % 10 == 0:
				count = 0

			# update display
			pygame.display.update()
			self.handleKey()
			# 10 fps
			self.clock.tick(10)
			count += 1
		# max play time exceeded
		self.close()
		logging.info("Display thread closed.")

