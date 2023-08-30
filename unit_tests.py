"""
Code for Unit Testing of the sputtering Anlage
SoSe 23
Luc Doppler - MECM
"""

# User Interface
from tkinter import *
import tkinter as tk
from tkinter import messagebox

# Communication with Arduino
import pyfirmata
from pyfirmata import util

import datetime
from timeit import default_timer as timer

import csv

# Variables
# Digital
ledState = 0
pumpeState = 0
turbo66State = 0
turboEinState = 0
generatorState = 0
# Pwm
argonState = 0
hochspannungState = 0

# Data logging
logging = False
ledStatelog = []
pumpeStatelog = []
turbo66Statelog = []
turboEinStatelog = []
generatorStatelog = []
argonStatelog = []
hochspannungStatelog = []

potiSchichtlog = []
potiStromlog = []
potiDrucklog = []
deckelschalterlog = []
TPSpeedlog = []
StromMessunglog = []
Drucklog = []
Druck2log = []

time = []

startTime = 0


def toggleLed():
    global ledState
    ledState ^= 1
    app.ledValue.config(text=str(ledState))
    app.board.led.write(ledState)
    return


def togglePumpe():
    global pumpeState
    pumpeState ^= 1
    app.pumpeValue.config(text=str(pumpeState))
    app.board.pumpe.write(pumpeState)
    return


def toggleTurbo66():
    global turbo66State
    turbo66State ^= 1
    app.turbo66Value.config(text=str(turbo66State))
    app.board.turbo66.write(turbo66State)
    return


def toggleGeneratorEin():
    global generatorState
    generatorState ^= 1
    app.generatorValue.config(text=str(generatorState))
    app.board.generator.write(generatorState)
    return


def toggleTurboEin():
    global turboEinState
    turboEinState ^= 1
    app.turboEinValue.config(text=str(turboEinState))
    app.board.turboEIN.write(turboEinState)
    return


def argonPlus():
    global argonState
    argonState += 0.01
    if argonState > 1:
        argonState = 1
    app.argonValue.config(text=str(argonState)[:5])
    app.board.argonVentil.write(argonState*12.55) # *12.55
    return


def argonMoins():
    global argonState
    argonState -= 0.01
    if argonState < 0:
        argonState = 0
    app.argonValue.config(text=str(argonState)[:5])
    app.board.argonVentil.write(argonState*12.55) # *12.55
    return


def spannungPlus():
    global hochspannungState
    hochspannungState += 0.05
    if hochspannungState > 1:
        hochspannungState = 1
    app.hochspannungValue.config(text=str(hochspannungState)[:5])
    app.board.hochspannung.write(hochspannungState)
    return


def spannungMinus():
    global hochspannungState
    hochspannungState -= 0.05
    if hochspannungState < 0:
        hochspannungState = 0
    app.hochspannungValue.config(text=str(hochspannungState)[:5])
    app.board.hochspannung.write(hochspannungState)
    return


def stop():
    app.board.turboEIN.write(0)
    app.board.turbo66.write(0)
    app.board.pumpe.write(0)
    app.board.led.write(0)
    app.board.generator.write(0)
    app.board.argonVentil.write(0)
    app.board.hochspannung.write(0)

    global ledState
    global pumpeState
    global turbo66State
    global turboEinState
    global argonState
    global generatorState

    ledState = 0
    pumpeState = 0
    turbo66State = 0
    turboEinState = 0
    argonState = 0
    generatorState = 0
    hochspannungState = 0

    app.ledValue.config(text=str(ledState))
    app.pumpeValue.config(text=str(pumpeState))
    app.turbo66Value.config(text=str(turbo66State))
    app.turboEinValue.config(text=str(turboEinState))
    app.generatorValue.config(text=str(generatorState))
    app.argonValue.config(text=str(argonState))
    app.hochspannungValue.config(text=(hochspannungState))

    # app.quit()
    return


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
        # return str(1.7*pow(10, 5*data-3.5))
        data = 5*data
        return str(1.7*pow(10, data - 3.5))[:8]


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


def toggleLog():
    global logging
    global startTime
    if logging:
        app.loggingLabel.config(text="Inaktiv", fg='red')
        # Save the logged data
        fields = ['ledState', 'pumpeState', 'turbo66State', 'turboEinState',
                  'generatorState', 'argonState', 'hochspannungState',
                  'potiSchicht', 'potiStrom', 'potiDruck', 'deckelschalter',
                  'TPSpeed', 'StromMessung', 'Druck', 'Druck2', 'time']
        rows = [ ledStatelog,
                 pumpeStatelog,
                 turbo66Statelog,
                 turboEinStatelog,
                 generatorStatelog,
                 argonStatelog,
                 hochspannungStatelog,
                 potiSchichtlog,
                 potiStromlog,
                 potiDrucklog,
                 deckelschalterlog,
                 TPSpeedlog,
                 StromMessunglog,
                 Drucklog,
                 Druck2log,
                 time]

        rows = list(map(list, zip(*rows)))
	
        name = './logs/' + datetime.datetime.now().strftime('Sputterlog_Test_%H_%M_%d_%m_%Y.csv')

        with open(name, 'w') as f:
            # using csv.writer method from CSV package
            write = csv.writer(f)

            write.writerow(fields)
            write.writerows(rows)

        logging = False
        pass
    else:
        logging = True
        app.loggingLabel.config(text="Aktiv", fg='green')
        startTime = timer()


def update():
    global startTime

    # emergency stop
    # if app.board.deckelschalter.read():
    #     stop()


    app.after(100, update)
    app.poti1Value.config(text=convert5V(app.board.potiSchicht.read()))
    app.poti2Value.config(text=convert5V(app.board.potiStrom.read()))
    app.poti3Value.config(text=convert5V(app.board.potiDruck.read()))

    app.deckelTasterValue.config(text=str(app.board.deckelschalter.read()))

    app.ledValue.config(text=str(ledState))
    app.pumpeValue.config(text=str(pumpeState))
    app.turbo66Value.config(text=str(turbo66State))
    app.turboEinValue.config(text=str(turboEinState))
    app.generatorValue.config(text=str(generatorState))

    app.TPSpeedValue.config(text=convertTPS(app.board.turbopumpe.read()))
    app.stromMessungValue.config(text=convertStrom(app.board.strom.read()/2))
    druckFein = app.board.druck.read()
    if druckFein is not None:
        if 5*druckFein < 4:
            app.druckValue.config(text=convertDruck(app.board.druck.read()))
        else:
            app.druckValue.config(text="Zu Hoch")
    else:
        app.druckValue.config(text="None")

    app.druck_2Value.config(text=convertDruck_2(app.board.druck2.read()))

    if logging:
        ledStatelog.append(ledState)
        pumpeStatelog.append(pumpeState)
        turbo66Statelog.append(turbo66State)
        turboEinStatelog.append(turboEinState)
        generatorStatelog.append(generatorState)
        argonStatelog.append(argonState)
        hochspannungStatelog.append(hochspannungState)
        potiSchichtlog.append(app.board.potiSchicht.read())
        potiStromlog.append(app.board.potiStrom.read())
        potiDrucklog.append(app.board.potiDruck.read())
        deckelschalterlog.append(app.board.deckelschalter.read())
        TPSpeedlog.append(app.board.turbopumpe.read())
        StromMessunglog.append(app.board.strom.read()/2)
        Drucklog.append(app.board.druck.read())
        Druck2log.append(app.board.druck2.read())
        time.append(timer() - startTime)
        return

class MyApplication(Tk):
    def __init__(self):
        # Init UI
        super().__init__()
        self.title("Sputteranlage - HKA µLabor - Unit testing")
        self.minsize(800, 460)

        self.userInputsA = tk.Label(self, text="USER INPUTS - Analog", fg='blue', font='Helvetica 12')
        self.userInputsA.grid(column=1, row=1)

        self.poti1 = tk.Label(self, text="Poti Schicht")
        self.poti1.grid(column=1, row=2)
        self.poti1Value = tk.Label(self, text="0")
        self.poti1Value.grid(column=2, row=2)

        self.poti2 = tk.Label(self, text="Poti Strom")
        self.poti2.grid(column=1, row=3)
        self.poti2Value = tk.Label(self, text="0")
        self.poti2Value.grid(column=2, row=3)

        self.poti3 = tk.Label(self, text="Poti Druck")
        self.poti3.grid(column=1, row=4)
        self.poti3Value = tk.Label(self, text="0")
        self.poti3Value.grid(column=2, row=4)

        self.userInputsD = tk.Label(self, text="USER INPUTS - Digital", fg='blue', font='Helvetica 12')
        self.userInputsD.grid(column=1, row=5)

        self.deckelTaster = tk.Label(self, text="Deckeltaster")
        self.deckelTaster.grid(column=1, row=6)
        self.deckelTasterValue = tk.Label(self, text="0")
        self.deckelTasterValue.grid(column=2, row=6)

        self.systemOutputD = tk.Label(self, text="SYSTEM OUTPUTS - Digital", fg='blue', font='Helvetica 12')
        self.systemOutputD.grid(column=1, row=7)

        self.led = tk.Label(self, text="LED")
        self.led.grid(column=1, row=8)
        self.ledValue = tk.Label(self, text=str(ledState))
        self.ledValue.grid(column=2, row=8)
        self.ledBtn = tk.Button(self, bd=4, bg='#90EE90', text="TOGGLE", command=toggleLed, font='Helvetica 8')
        self.ledBtn.grid(column=3, row=8)

        self.pumpe = tk.Label(self, text="Pumpe")
        self.pumpe.grid(column=1, row=9)
        self.pumpeValue = tk.Label(self, text=str(pumpeState))
        self.pumpeValue.grid(column=2, row=9)
        self.pumpeBtn = tk.Button(self, bd=4, bg='#90EE90', text="TOGGLE", command=togglePumpe, font='Helvetica 8')
        self.pumpeBtn.grid(column=3, row=9)

        self.turbo66 = tk.Label(self, text="Turbo66")
        self.turbo66.grid(column=1, row=10)
        self.turbo66Value = tk.Label(self, text="0")
        self.turbo66Value.grid(column=2, row=10)
        self.turbo66Btn = tk.Button(self, bd=4, bg='#90EE90', text="TOGGLE", command=toggleTurbo66, font='Helvetica 8')
        self.turbo66Btn.grid(column=3, row=10)

        self.turboEin = tk.Label(self, text="TurboEin")
        self.turboEin.grid(column=1, row=11)
        self.turboEinValue = tk.Label(self, text="0")
        self.turboEinValue.grid(column=2, row=11)
        self.turboEinBtn = tk.Button(self, bd=4, bg='#90EE90', text="TOGGLE", command=toggleTurboEin, font='Helvetica 8')
        self.turboEinBtn.grid(column=3, row=11)

        self.generator = tk.Label(self, text="Generator")
        self.generator.grid(column=1, row=12)
        self.generatorValue = tk.Label(self, text="0")
        self.generatorValue.grid(column=2, row=12)
        self.generatorBtn = tk.Button(self, bd=4, bg='#90EE90', text="TOGGLE", command=toggleGeneratorEin, font='Helvetica 8')
        self.generatorBtn.grid(column=3, row=12)

        self.systemOutputD = tk.Label(self, text="SYSTEM OUTPUTS - PWM", fg='blue', font='Helvetica 12')
        self.systemOutputD.grid(column=1, row=13)

        self.argon = tk.Label(self, text="Argon Ventil")
        self.argon.grid(column=1, row=14)
        self.argonValue = tk.Label(self, text="0")
        self.argonValue.grid(column=2, row=14)
        self.turboEinBtn = tk.Button(self, bd=4, bg='#90EE90', text="-", command=argonMoins, font='Helvetica 8')
        self.turboEinBtn.grid(column=3, row=14)
        self.turboEinBtn2 = tk.Button(self, bd=4, bg='#90EE90', text="+", command=argonPlus, font='Helvetica 8')
        self.turboEinBtn2.grid(column=4, row=14)

        self.hochspannung = tk.Label(self, text="Hochspannung")
        self.hochspannung.grid(column=1, row=15)
        self.hochspannungValue = tk.Label(self, text="0")
        self.hochspannungValue.grid(column=2, row=15)
        self.hochspannungBtn = tk.Button(self, bd=4, bg='#90EE90', text="-", command=spannungMinus, font='Helvetica 8')
        self.hochspannungBtn.grid(column=3, row=15)
        self.hochspannungBtn2 = tk.Button(self, bd=4, bg='#90EE90', text="+", command=spannungPlus, font='Helvetica 8')
        self.hochspannungBtn2.grid(column=4, row=15)

        self.systemInputsA = tk.Label(self, text="SYSTEM INPUTS - Analog", fg='blue', font='Helvetica 12')
        self.systemInputsA.grid(column=5, row=1)

        self.TPSpeed = tk.Label(self, text="TPSpeed")
        self.TPSpeed.grid(column=5, row=2)
        self.TPSpeedValue = tk.Label(self, text="0")
        self.TPSpeedValue.grid(column=6, row=2)

        self.stromMessung = tk.Label(self, text="Strom Messung")
        self.stromMessung.grid(column=5, row=3)
        self.stromMessungValue = tk.Label(self, text="0")
        self.stromMessungValue.grid(column=6, row=3)

        self.druck = tk.Label(self, text="Druck")
        self.druck.grid(column=5, row=4)
        self.druckValue = tk.Label(self, text="0")
        self.druckValue.grid(column=6, row=4)

        self.druck_2 = tk.Label(self, text="Druck/2")
        self.druck_2.grid(column=5, row=5)
        self.druck_2Value = tk.Label(self, text="0")
        self.druck_2Value.grid(column=6, row=5)

        self.loggingBtn = tk.Button(self, bd=4, bg='#90EE90', text="Logging", command=toggleLog, font='Helvetica 14')
        self.loggingBtn.grid(column=6, row=6)

        self.loggingLabel = tk.Label(self, text="Inaktiv", fg='red', font='Helvetica 14')
        self.loggingLabel.grid(column=6, row=8)

        # Init Arduino
        self.board = pyfirmata.ArduinoMega('/dev/ttyACM0')
        self.it = util.Iterator(self.board)
        self.it.start()

        # Analog Pins Enable
        self.board.analog[1].enable_reporting()
        self.board.analog[2].enable_reporting()
        self.board.analog[3].enable_reporting()
        self.board.analog[4].enable_reporting()
        self.board.analog[5].enable_reporting()
        self.board.analog[7].enable_reporting()
        self.board.analog[8].enable_reporting()

        # Analog Pins Input
        self.board.turbopumpe = self.board.get_pin('a:1:i')
        self.board.strom = self.board.get_pin('a:2:i')
        self.board.potiSchicht = self.board.get_pin('a:3:i')
        self.board.potiStrom = self.board.get_pin('a:4:i')
        self.board.potiDruck = self.board.get_pin('a:5:i')
        self.board.druck2 = self.board.get_pin('a:7:i')
        self.board.druck = self.board.get_pin('a:8:i')

        # Digital Pins Input
        self.board.deckelschalter = self.board.get_pin('d:19:i')

        # Digital Pins Output
        self.board.turboEIN = self.board.get_pin('d:18:o')
        self.board.turbo66 = self.board.get_pin('d:17:o')
        self.board.pumpe = self.board.get_pin('d:16:o')
        self.board.led = self.board.get_pin('d:15:o')
        self.board.generator = self.board.get_pin('d:14:o')

        # PWM Pins Output
        self.board.argonVentil = self.board.get_pin('d:3:p')
        self.board.hochspannung = self.board.get_pin('d:4:p')

        self.board.argonVentil.write(0);
        self.board.hochspannung.write(0);

        # SAFETY SHUTDOWN
        self.emergencyStop = tk.Button(self, bd=4, bg='red', text="EMERGENCY STOP", command=stop, font='Helvetica 10')
        self.emergencyStop.grid(column=5, row=10)

        self.turboEinBtn = tk.Button(self, bd=4, bg='#90EE90', text="+", command=argonPlus, font='Helvetica 8')
        self.turboEinBtn.grid(column=4, row=14)



app = MyApplication()
update()
app.mainloop()