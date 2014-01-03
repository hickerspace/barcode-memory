#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygame, pygame.event, pygame.mouse
from datetime import timedelta
import os, threading, logging
from memory import Memory
import time

DEBUG = True
SCANNER_SENDS_RETURN = False
BARCODE_LENGTH = 2 #13

class MemoryDisplay(threading.Thread):
	"Displays timer and memory images. Handles barcode input (barcode scanner is a HID)."

	# taken from http://learn.adafruit.com/pi-video-output-using-pygame/pygame-drawing-functions
	def __init__(self, ledstrip):
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
		self.maxPlayTime = 400
		self.lastHighscore = []
		self.barcode = ""
		self.runGame = True
		self.lastImg = None

		self.white = (255, 255, 255)
		self.black = (0, 0, 0)
		self.red = (255, 0, 0)
		self.green = (0, 255, 0)

		self.ledstrip = ledstrip
		self.memory = Memory(self)

		# preload images
		gameImgs = ["byhickerspace.png", "qrcode.png"]
		self.preloadedImgs = {}
		for imgPath in gameImgs:
			self.preloadedImgs[imgPath] = pygame.image.load(imgPath).convert()

		for imgPath in self.memory.images:
			img = pygame.image.load(imgPath).convert()
			self.preloadedImgs[imgPath] = self.scalePercentage(img, 1)

		# Clear the screen to start
		self.screen.fill((0, 0, 0))
		# Initialise font support
		pygame.font.init()
		# hide mouse pointer
		pygame.mouse.set_visible(False)
		# Render the screen
		pygame.display.update()

		self.endGame()

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
		self.screen.blit(self.preloadedImgs[img], (0, 25))

		if firstMove:
			self.lastImg = img
		else:
			pass
			#secondary = pygame.image.load(self.lastImg).convert()
			#secondary = self.scalePercentage(secondary, 0.25)
			#self.screen.blit(secondary, (self.screen.get_rect().width-secondary.get_rect().width, 25))

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

		pygame.display.update()

	def endGame(self):
		self.inGame = False
		self.highscore()

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
					if not SCANNER_SENDS_RETURN and len(self.barcode) == 13:
						logging.info("Barcode %s received." % self.barcode)
						self.memory.scan(self.barcode)
						self.barcode = ""

	def close(self):
		self.runGame = False
		# stop other threads
		self.ledstrip.close()

	def blitCenterX(self, surface, y):
		pos = surface.get_rect()
		pos.centerx = self.screen.get_rect().centerx
		pos.y = y
		self.screen.blit(surface, pos)

	def highscore(self):

		self.ledstrip.animation(self.memory.barcodepositions.values())

		# clear screen
		self.screen.fill(self.black)
		#titleFont = pygame.font.Font(None, 60)
		#titleSurface = titleFont.render("Barcode Memory", True, white, black)
		#self.blitCenterX(titleSurface, 160)

		font = pygame.font.Font(None, 32)

		if self.playTime > 0 and self.playTime <= self.maxPlayTime:
		 	time_ = str(timedelta(seconds=self.playTime))[2:]
			personal = font.render("Congratulations, your score: %s" % time_, True, self.red, self.black)
			self.blitCenterX(personal, 185)

		pos = 230
		rank = 1
		for score in self.memory.loadHighscore()[:8]:
			delta, playTime = score
			scoreline = font.render("#%d      %s      %s" % (rank, str(delta)[2:], playTime.strftime("%Y-%m-%d %H:%M")), True, self.white, self.black)
			self.blitCenterX(scoreline, pos)
			pos += 25
			rank += 1

		self.blitCenterX(self.preloadedImgs["byhickerspace.png"], 0)
		self.blitCenterX(self.preloadedImgs["qrcode.png"], 600)

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
				pygame.display.update()

				if count % 10 == 0:
					self.playTime += 1
			else:
				if count == 3:
					self.blitCenterX(font.render("Scan NEW GAME to play!", True, self.green, self.black), 440)
					# update display
					pygame.display.update()
				elif count == 10:
					self.blitCenterX(font.render("Scan NEW GAME to play!", True, self.black, self.black), 440)
					# update display
					pygame.display.update()

			if count % 10 == 0:
				count = 0

			self.handleKey()
			# 10 fps
			self.clock.tick(10)
			count += 1
		# max play time exceeded
		self.close()
		logging.info("Display thread closed.")

