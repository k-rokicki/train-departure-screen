import os
import sys
import time
import json

from datetime import timedelta
from timeloop import Timeloop
from datetime import datetime
from PIL import ImageFont, Image
from helpers import get_device
from buses import loadDepartures
from luma.core.render import canvas
from luma.core.virtual import viewport, snapshot


def loadConfig():
    with open('config.json', 'r') as jsonConfig:
        data = json.load(jsonConfig)
        return data


def makeFont(name, size):
    font_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'fonts',
            name
        )
    )
    return ImageFont.truetype(font_path, size)


def renderLine(departure):
    def drawText(draw, width, height):
        line = '   ' + departure["linia"]

        draw.text((0, 0), text=line, font=font, fill="yellow")

    return drawText


def renderDestination(departure):
    def drawText(draw, width, height):
        destination = '     ' + departure["kierunek"]

        draw.text((0, 0), text=destination, font=font, fill="yellow")

    return drawText


def renderDepartureTime(departure):
    def drawText(draw, width, height):
        departureTime = departure["odjazd"]

        draw.text((0, 0), text=departureTime, font=font, fill="yellow")

    return drawText


def renderTime(draw, width, height):
    rawTime = datetime.now().time()
    hour, minute, second = str(rawTime).split('.')[0].split(':')

    draw.text(((width - 56) / 2, 0), text="{}:{}".format(hour, minute),
              font=fontBoldLarge, fill="yellow")


def loadData(apiConfig, journeyConfig, linesInfo):
    departures = loadDepartures(
        journeyConfig, linesInfo, apiConfig["resourceID"], apiConfig["apiKey"])

    if len(departures) == 0:
        return False

    return departures


def drawSignage(device, width, height, data, first):
    device.clear()

    virtualViewport = viewport(device, width=width, height=height)

    status = "59 min   "
    lineExample = "504   "

    departures = data

    width = virtualViewport.width

    # First measure the text size
    with canvas(device) as draw:
        w, h = draw.textsize(status, font)

    with canvas(device) as draw:
        w1, h1 = draw.textsize(lineExample, font)

    startIndex = 0 + 3 * (0 if first or len(departures) <= 3 else 1)

    if len(departures) > startIndex:
        row1A = snapshot(w1, 16, renderLine(
            departures[startIndex + 0]), interval=10)
        row1B = snapshot(width - w - w1, 16, renderDestination(
            departures[startIndex + 0]), interval=10)
        row1C = snapshot(w, 16, renderDepartureTime(
            departures[startIndex + 0]), interval=10)

    if len(departures) > startIndex + 1:
        row2A = snapshot(w1, 16, renderLine(
            departures[startIndex + 1]), interval=10)
        row2B = snapshot(width - w - w1, 16, renderDestination(
            departures[startIndex + 1]), interval=10)
        row2C = snapshot(w, 16, renderDepartureTime(
            departures[startIndex + 1]), interval=10)

    if len(departures) > startIndex + 2:
        row3A = snapshot(w1, 16, renderLine(
            departures[startIndex + 2]), interval=10)
        row3B = snapshot(width - w - w1, 16, renderDestination(
            departures[startIndex + 2]), interval=10)
        row3C = snapshot(w, 16, renderDepartureTime(
            departures[startIndex + 2]), interval=10)

    rowTime = snapshot(width, 14, renderTime, interval=1)

    if len(virtualViewport._hotspots) > 0:
        for hotspot, xy in virtualViewport._hotspots:
            virtualViewport.remove_hotspot(hotspot, xy)

    if len(departures) > startIndex + 0:
        virtualViewport.add_hotspot(row1A, (0, 0 + 0))
        virtualViewport.add_hotspot(row1B, (w1, 0 + 0))
        virtualViewport.add_hotspot(row1C, (width - w, 0 + 0))
    
    if len(departures) > startIndex + 1:
        virtualViewport.add_hotspot(row2A, (0, 0 + 16))
        virtualViewport.add_hotspot(row2B, (w1, 0 + 16))
        virtualViewport.add_hotspot(row2C, (width - w, 0 + 16))

    if len(departures) > startIndex + 2:
        virtualViewport.add_hotspot(row3A, (0, 0 + 32))
        virtualViewport.add_hotspot(row3B, (w1, 0 + 32))
        virtualViewport.add_hotspot(row3C, (width - w, 0 + 32))

    virtualViewport.add_hotspot(rowTime, (0, 50))

    return virtualViewport


try:
    config = loadConfig()

    device = get_device()
    font = makeFont("Dot Matrix Regular.ttf", 16)
    fontBold = makeFont("Dot Matrix Bold.ttf", 16)
    fontBoldLarge = makeFont("Dot Matrix Bold.ttf", 20)

    widgetWidth = 256
    widgetHeight = 64

    data = loadData(config["apiZTM"], config["busStopInfo"], config["linesInfo"])
    
    virtual = drawSignage(device, width=widgetWidth,
                            height=widgetHeight, data=data, first=True)

    timeAtStart = time.time()
    timeNow = time.time()
    drawFirst = False
    drawSecond = False
    secondSwitch = 0

    while True:
        if (timeNow - timeAtStart >= config["refreshTime"] / 2):
            if secondSwitch == 0:
                drawSecond = True
                secondSwitch = 1

            if (timeNow - timeAtStart >= config["refreshTime"]):
                data = loadData(config["apiZTM"], config["busStopInfo"], config["linesInfo"])
                timeAtStart = time.time()
                drawFirst = True
                secondSwitch = 0

            if drawFirst:
                virtual = drawSignage(device, width=widgetWidth,
                                        height=widgetHeight, data=data, first=True)
                drawFirst = False

            if drawSecond:
                virtual = drawSignage(device, width=widgetWidth,
                                        height=widgetHeight, data=data, first=False)
                drawSecond = False
        
        timeNow = time.time()
        virtual.refresh()


except KeyboardInterrupt:
    pass
except ValueError as err:
    print(f"Error: {err}")
except KeyError as err:
    print(f"Error: Please ensure the {err} environment variable is set")
