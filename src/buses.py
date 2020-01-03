import os
import requests
import datetime
from unidecode import unidecode

def loadDepartures(journeyConfig, linesInfo, resourceID, apiKey):
    busStopID = journeyConfig["busStopID"]

    now = datetime.datetime.now()
    now = now.replace(second=0)
    now = now.replace(microsecond=0)

    departures = []

    for line in linesInfo:
        URL = f"https://api.um.warszawa.pl/api/action/dbtimetable_get/?id={resourceID}&busstopId={busStopID}&busstopNr={linesInfo[line]}&line={line}&apikey={apiKey}"

        r = requests.get(url=URL)

        data = r.json()['result']

        bestDiffMin = float('inf')

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

                #if (diffMin > 90):
                #    continue

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

        try:
            departures.append(departure)
        except NameError:
            pass
    
    #print(departures)
    departures.sort(key=lambda x: x['czas'])

    return departures
