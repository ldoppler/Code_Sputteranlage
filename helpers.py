"""
Helpers functions for the sputtering project
"""


def convert5V(data):
    if data is None:
        return str(0)
    else:
        return str(5*data)[:4]


def convertByte(data):
    if data is None:
        return str(0)
    else:
        return str(round(255 * data))[:4]


def convertDruck(data):
    if data is None:
        return str(0)
    else:
        data = 5*data
        return str(1.7*pow(10, data - 3.5))[:8]


def getTPS(data):
    if data is None:
        return 0
    else:
        return round(100*data)


def convertTPS(data):
    if data is None:
        return str(0)
    else:
        return str(round(100*data))[:4]


def convertDruck_2(data):
    if data is None:
        return str(0)
    else:
        data = 2*5*data
        return str(1.7*pow(10, data - 3.5))[:8]


def convertStrom(data):
    if data is None:
        return str(0)
    else:
        data = 100*data
        return str(data)[:4]


def getSollStrom(data):
    if data is None:
        return 0
    else:
        return 50*data


def convertSollStrom(data):
    if data is None:
        return str(0)
    else:
        data = 50*data
        return str(data)[:4]


def convertSollSchicht(data):
    if data is None:
        return str(0)
    else:
        data = 200*data
        return str(data)[:4]


def convertSollDruck(data):
    if data is None:
        return str(0)
    else:
        data = 20*data
        if data < 0.7:
            data = 0.7
        return str(data)[:4]


def getDruck_2(data):
    if data is None:
        return 0
    else:
        data = 2*5*data
        return 1.7*pow(10, data - 3.5)


def getSollDruck2(data):
    if data is None:
        return 0
    else:
        data = 20*data
        if data < 0.7:
            data = 0.7
        return data


def limitDA(data):
    if data < 0.2:
        return 0.2
    elif data > 1:
        return 1
    else:
        return data


def getStrom(data):
    if data is None:
        return 0
    else:
        return 100*data
