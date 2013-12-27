#!/bin/env/python
# -*- coding: utf-8 -*-

import serial
import ConfigParser
import random
import os
import logging
import datetime

class Memory(object):

    def __init__(self, display=None):

        self.config = ConfigParser.SafeConfigParser()
        self.config.read("config")

        self.display = display

        self.memoryfile = self.config.get("memory","memoryfile")

        self.barcodes = []
        self.barcodepairs = {}

        self.images = []
        self.barcodeimages = {}

        self.barcodepositions = {} #<barcode> : <position on led-stripe [0,50]>

        self.temp_barcode = None

        try:
            self.printer = serial.Serial(self.config.get("printer", "port"), self.config.get("printer", "baudrate"))
        except Exception as e:
            logging.exception("Exception because of unavailability of serial receipt printer.")


        self.preset_barcodes = {
            self.config.get("preset_barcodes", "reset"):self._reset,
            self.config.get("preset_barcodes", "print"):self._print,
        }

        self._load_images()
        self._reset(True)


    def scan(self, barcodeinput):

        if barcodeinput in self.preset_barcodes:
            self.preset_barcodes[barcodeinput]()
        else:
            self.inputbarcode(barcodeinput)


    def _load_images(self):

        files = os.listdir(self.config.get("memory", "imagedir"))

        for f in files:
            if f not in self.images:
                self.images.append(os.path.join(self.config.get("memory", "imagedir"), f))


    def _reset(self, firstRun=False):

        logging.info("Reset started.")

        self.barcodes = []
        self.barcodepairs = {}
        # reset in case RESET got scanned during move
        self.temp_barcode = None

        # load barcodes
        with open(self.memoryfile) as f:
            for line in f:
                line = line.strip()
                if len(line) > 0:
                    if line not in self.barcodes and line not in self.preset_barcodes and line[0] != "#":

                        tmptuple = line.split(";")
                        self.barcodepositions[tmptuple[0]] = int(tmptuple[1])
                        self.barcodes.append(tmptuple[0])

        # delete last element if list contains an odd amount of elements
        if len(self.barcodes) % 2 != 0:
            del self.barcodes[-1]

        # randomize list
        random.shuffle(self.barcodes)
        random.shuffle(self.images)

        if len(self.barcodes) / 2 > len(self.images):
            logging.warn("More barcodes than images inserted.")

        # make pairs from list
        for i in range(0, len(self.barcodes)-1, 2):
            self.barcodepairs[self.barcodes[i]] = self.barcodes[i+1]
            self.barcodepairs[self.barcodes[i+1]] = self.barcodes[i]

            tmp_i = int( (i / 2)+0.5 )
            self.barcodeimages[self.barcodes[i]] = self.images[tmp_i]
            self.barcodeimages[self.barcodes[i+1]] = self.images[tmp_i]

        if self.display and not firstRun:
            #  make all LEDs red
            for led in self.barcodepositions.values():
                self.display.ledstrip.sendRed(led)

            self.display.newGame()


    def inputbarcode(self, barcodeinput):

            logging.debug("Scanning barcode %s." % barcodeinput)

            if barcodeinput not in self.barcodepairs and barcodeinput not in self.preset_barcodes:
                logging.info("Barcode unknown. Try again.")

            elif barcodeinput in self.barcodes: # if not already found

                firstMove = self.temp_barcode == None
                # make led yellow
                self.display.ledstrip.sendYellow(self.barcodepositions[barcodeinput])
                # show image
                self.display.showImg(self.barcodeimages[barcodeinput], firstMove)

                if firstMove: # first scanned barcode
                    self.temp_barcode = barcodeinput

                else: # second scanned barcode

                    if self.barcodepairs[barcodeinput] == self.temp_barcode:
                        logging.info("Pair found.")
                        # turn LED green
                        self.display.ledstrip.sendGreen(self.barcodepositions[barcodeinput])
                        self.display.ledstrip.sendGreen(self.barcodepositions[self.temp_barcode])

                        # delete found pair out of list of barcodes
                        self.barcodes.remove(barcodeinput)
                        self.barcodes.remove(self.temp_barcode)

                        self.temp_barcode = None

                        if len(self.barcodes) == 0:
                            logging.info("All Pairs found, please scan reset.")
                            self.saveHighscore(self.display.playTime)
                            self.display.endGame()

                    else:
                        logging.info("No pair. Try again.")

                        # turn leds yellow
                        self.display.ledstrip.sendRed(self.barcodepositions[barcodeinput])
                        self.display.ledstrip.sendRed(self.barcodepositions[self.temp_barcode])

                        self.temp_barcode = None


    def _print(self):
        self.printer.write("\x1d\x77\x04")
        self.printer.write("\x1d\x68\xff")
        for i in self.barcodes:
            self.printer.write("\x1d\x6b\x02%s\00" % i)
            self.printer.write("\n\n\n\n")

        # cut & go
        self.printer.write("\x1b\x4A\x9C\x1b\x69")

    def loadHighscore(self):
        highscores_str = [] # list of string highscores
        highscores = [] # list of tuple highscores (timedelta, datetime)

        with open(self.config.get("memory","highscorefile")) as f:
            for line in f:
                line = line.strip()

                if len(line) > 0:
                    if line not in highscores_str and line[0] != "#":

                        tmptuple = line.split(";")

                        highscores_str.append(line)
                        highscores.append( ( datetime.timedelta(seconds=int(tmptuple[0])) , datetime.datetime.strptime(tmptuple[1], "%Y-%m-%d %H:%M") ) )

        # sort by timedelta seconds
        return sorted(highscores, key=lambda score: score[0].seconds)


    def saveHighscore(self, seconds):
        with open(self.config.get("memory","highscorefile"), "a") as f:
            f.write("%s;%s\n" % (seconds, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))


def main():
    "For testing purposes only."
    m = Memory()

    while 1:
        barcodeinput = raw_input("> ")
        m.scan(barcodeinput)
        #m.printbarcode(barcodeinput)


if __name__ == "__main__":
    main()
