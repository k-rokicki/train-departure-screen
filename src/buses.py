import os
import requests
import datetime
from unidecode import unidecode

loadedData = {}

def loadDepartures(journeyConfig, linesInfo, resourceID, apiKey, reloadData):
    busStopID = journeyConfig["busStopID"]

    now = datetime.datetime.now()
    now = now.replace(second=0)
    now = now.replace(microsecond=0)

    departures = []

    for line in linesInfo:
        if reloadData:
            URL = f"https://api.um.warszawa.pl/api/action/dbtimetable_get/?id={resourceID}&busstopId={busStopID}&busstopNr={linesInfo[line]}&line={line}&apikey={apiKey}"
            r = requests.get(url=URL)
            loadedData[line] = r.json()['result']
        
        data = loadedData[line]

        bestDiffMin = float('inf')
        departure = None

        for entry in data:
            info = {}
            values = entry['values']

            for value in values:
                if value['key'] == 'kierunek' or value['key'] == 'czas':
                    info[value['key']] = value['value']

            time = datetime.datetime.now()
            timeArr = info['czas'].split(':')

            if int(timeArr[0]) >= 24 and now.hour > 7:
                time = time + datetime.timedelta(days=1)

            time = time.replace(hour=(int(timeArr[0]) if int(timeArr[0]) < 24 else int(timeArr[0]) - 24))
            time = time.replace(minute=int(timeArr[1]))
            time = time.replace(second=0)
            time = time.replace(microsecond=0)

            if (now < time):
                diffMs = time - now
                diffMin = int(diffMs.total_seconds() / 60)

                if (diffMin > 120):
                    continue

                if diffMin < bestDiffMin:
                    bestDiffMin = diffMin

                    if (diffMin < 60):
                        if (diffMin == 1):
                            departureTime = '< ' + str(diffMin) + ' min'
                        else:
                            departureTime = str(diffMin) + ' min'
                    else:
                        hour = timeArr[0] if int(timeArr[0]) < 24 else str(int(timeArr[0]) - 24)
                        minute = timeArr[1]
                        departureTime = hour + ':' + minute

                    departure = {
                        'linia': line,
                        'kierunek': unidecode(info['kierunek']),
                        'czas': time,
                        'odjazd': departureTime
                    }

        if departure is not None:
            try:
                departures.append(departure)
            except NameError:
                pass
    
    departures.sort(key=lambda x: x['czas'])

    return departures
