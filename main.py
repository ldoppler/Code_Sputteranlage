"""
Code for Sputtering
SoSe 23
Luc Doppler - MECM
"""

from tkinter import *
import tkinter as tk
from tkinter import messagebox

import pyfirmata
from pyfirmata import util

from timeit import default_timer as timer

import csv

import datetime

from helpers import *

# Variables
# Digital
ledState = 0
pumpeState = 0
turbo66State = 0
turboEinState = 0
generatorState = 0
# Pwm
argonState = 0
hochspannungState = 0.4
# helpers
notaus = False
state = "Initial"
initial = True
spuehlCount = 0
shutdown = False
schichtdicke = 0
schichtTime0 = 0
schichtTime1 = 0


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


def helpme():
    tk.messagebox.showinfo(title="Help", message="UI zur Sputtering Anlage des µLabor der HKA\n"
                                                 "Ziel ist die Sputtering Anlage zu Steuern\nSoSe 2023")


def aboutme():
    tk.messagebox.showinfo(title="About", message="Alpha version")


def toggle_log():
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

        name = './logs/' + datetime.datetime.now().strftime('Sputterlog_%H_%M_%d_%m_%Y.csv')

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
    global hochspannungState

    ledState = 0
    pumpeState = 0
    turbo66State = 0
    turboEinState = 0
    argonState = 0
    generatorState = 0
    hochspannungState = 0
    return


def regeln_strom():
    global hochspannungState
    istStrom = getStrom(app.board.strom.read()/2)
    sollStrom = getSollStrom(app.board.potiStrom.read())
    if abs(istStrom - sollStrom) < 0.3:
        return
    else:
        hochspannungState = limitDA(hochspannungState + 0.002*(sollStrom - istStrom))
    app.board.hochspannung.write(hochspannungState)


def regeln_druck():
    global argonState
    ist_druck = getDruck_2(app.board.druck2.read())
    soll_druck = getSollDruck2(app.board.potiDruck.read())
    if abs(ist_druck - soll_druck) < 0.3:
        return
    else:
        argonState = limitDA(argonState + 0.005*(soll_druck - ist_druck))
    app.spuehlenRateLabel.config(text=str(100*argonState))
    app.board.argonVentil.write(argonState*12.55)


def reset_notaus():
    global notaus
    notaus = False
    return


def update():
    global startTime
    global notaus
    global state
    global initial
    global spuehlCount
    global argonState
    global generatorState
    global shutdown
    global schichtdicke
    global schichtTime0
    global schichtTime1

    app.after(100, update)

    if initial:
        initial = False
        return

    if state == "Initial":
        state = "checkTPR"
    if state == "Idle":
        # nur debug
        schichtTime0 = timer()
        # Alles aus
        stop()
        if app.board.deckelschalter is not None:
            if not app.board.deckelschalter.read() and not notaus:
                state = "Pumpe"
    elif state == "Pumpe":
        app.board.pumpe.write(1)
        if getDruck_2(app.board.druck2.read()) < 280:
            state = "Turbo"
    elif state == "Turbo":
        app.board.turbo66.write(1)
        app.board.turboEIN.write(1)
        app.board.led.write(1)
        if getTPS(app.board.turbopumpe.read()) > 65:
            state = "Spuehlen"
    elif state == "Spuehlen":
        app.board.led.write(0)
        argonState = 0.7
        app.board.argonVentil.write(argonState*12.55)
        app.spuehlenRateLabel.config(text=str(argonState*100))
        spuehlCount += 1
        if spuehlCount > 100:
            state = "WartenDruck"
            argonState = 0.4
            app.board.argonVentil.write(argonState*12.55)
            app.spuehlenRateLabel.config(text=str(argonState*100))
    elif state == "WartenDruck":
        regeln_druck()
        if abs(getDruck_2(app.board.druck2.read()) - getSollDruck2(app.board.potiDruck.read())) < 0.3:
            state = "Zunden"
            schichtTime1 = timer() # init timer
    elif state == "Zunden":
        app.board.led.write(1)
        schichtdicke += (timer() - schichtTime1) * app.board.strom.read()/2 * 255 / 500
        schichtTime1 = timer()
        app.board.generator.write(1)
        regeln_druck()
        generatorState = True
        regeln_strom()
        if getStrom(app.board.strom.read()) > 99: # zu viel Strom
            state = "Ueberstrom"
        if schichtdicke > 200*app.board.potiSchicht.read() :
            state = "Schicht_Fertig"
    elif state == "Schicht_Fertig":
        stop()
        if getTPS(app.board.turbopumpe.read()) < 2:
            state = "Idle"
            shutdown = True
            notaus = True
    elif state == "Ueberstrom":
        # current is too high
        stop()
    elif state == "checkTPR":
        # Check if problem with sensor or if the sensor is missing
        if app.board.druck2.read() < 0.15 or app.board.druck2.read() > 0.90:
            state = "TPR_defekt"
        else:
            state = "Idle"
    elif state == "TPR_defekt":
        # Stay in the loop and wait to resolve the sensor problem
        stop()

    # Schwarzer taster als notaus nutzen
    if app.board.deckelschalter.read():
        if state != "Idle" and shutdown:
            notaus = True
            state = "Idle"
            stop()
        if not shutdown:
            shutdown = True
    else:
        shutdown = False

    if generatorState:
        hochspannungValue = hochspannungState # 500 + 4*255*hochspannungState
    else:
        hochspannungValue = 0

    app.sollSchichtValueLabel.config(text=convertSollSchicht(app.board.potiSchicht.read()))
    app.sollStromValueLabel.config(text=convertSollStrom(app.board.potiStrom.read()))
    app.sollDruckValueLabel.config(text=convertSollDruck(app.board.potiDruck.read()))

    app.istSchichtValueLabel.config(text=str(schichtdicke)[:4]) # To store in a variable, is calculated
    app.istStromValueLabel.config(text=str(getStrom(app.board.strom.read()/2))[:4])
    app.istDruckValueLabel.config(text=convertDruck_2(app.board.druck2.read()))
    app.istSpannungValueLabel.config(text=str(hochspannungValue))
    app.istTPValueLabel.config(text=convertTPS(app.board.turbopumpe.read()))
    app.spuehlenRateLabel.config(text=str(argonState * 100))

    app.stateLabelValue.config(text=state)
    app.statusNotausLabelValue.config(text=str(notaus))

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
        StromMessunglog.append(app.board.strom.read())
        Drucklog.append(app.board.druck.read())
        Druck2log.append(app.board.druck2.read())
        time.append(timer() - startTime)
        return

class MyApplication(Tk):
    def __init__(self):
        super().__init__()
        self.title("Sputteranlage - HKA µLabor")
        self.minsize(800, 460)

        self.istLabelTitle = tk.Label(self, text="Live Werte", font='Helvetica 28 bold')
        self.istLabelTitle.grid(column=6, row=1)

        self.sollLabelTitle = tk.Label(self, text="Soll Werte", font='Helvetica 28 bold')
        self.sollLabelTitle.grid(column=2, row=1)

        self.sollSchichtLabel = tk.Label(self, text="Schichtdicke :", font='Helvetica 14')
        self.sollSchichtLabel.grid(column=1, row=2)
        self.sollSchichtValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.sollSchichtValueLabel.grid(column=2, row=2)
        self.sollSchichtUnit = tk.Label(self, text="nm", font='Helvetica 14')
        self.sollSchichtUnit.grid(column=3, row=2)

        self.sollStromLabel = tk.Label(self, text="Strom :", font='Helvetica 14')
        self.sollStromLabel.grid(column=1, row=3)
        self.sollStromValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.sollStromValueLabel.grid(column=2, row=3)
        self.sollStromUnit = tk.Label(self, text="mA", font='Helvetica 14')
        self.sollStromUnit.grid(column=3, row=3)

        self.sollDruckLabel = tk.Label(self, text="Druck :", font='Helvetica 14')
        self.sollDruckLabel.grid(column=1, row=4)
        self.sollDruckValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.sollDruckValueLabel.grid(column=2, row=4)
        self.sollDruckUnit = tk.Label(self, text="Pa", font='Helvetica 14')
        self.sollDruckUnit.grid(column=3, row=4)

        # ---------------------------------------------------------

        self.istSchichtLabel = tk.Label(self, text="Schichtdicke :", font='Helvetica 14')
        self.istSchichtLabel.grid(column=5, row=2)
        self.istSchichtValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.istSchichtValueLabel.grid(column=6, row=2)
        self.istSchichtUnit = tk.Label(self, text="nm", font='Helvetica 14')
        self.istSchichtUnit.grid(column=7, row=2)

        self.istStromLabel = tk.Label(self, text="Strom :", font='Helvetica 14')
        self.istStromLabel.grid(column=5, row=3)
        self.istStromValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.istStromValueLabel.grid(column=6, row=3)
        self.istStromUnit = tk.Label(self, text="mA", font='Helvetica 14')
        self.istStromUnit.grid(column=7, row=3)

        self.istDruckLabel = tk.Label(self, text="Druck :", font='Helvetica 14')
        self.istDruckLabel.grid(column=5, row=4)
        self.istDruckValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.istDruckValueLabel.grid(column=6, row=4)
        self.istDruckUnit = tk.Label(self, text="Pa", font='Helvetica 14')
        self.istDruckUnit.grid(column=7, row=4)

        self.istSpannungLabel = tk.Label(self, text="Spannung PWM :", font='Helvetica 14')
        self.istSpannungLabel.grid(column=5, row=5)
        self.istSpannungValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.istSpannungValueLabel.grid(column=6, row=5)
        self.istSpannungUnit = tk.Label(self, text="%", font='Helvetica 14')
        self.istSpannungUnit.grid(column=7, row=5)

        self.istTPLabel = tk.Label(self, text="Turbopumpe:", font='Helvetica 14')
        self.istTPLabel.grid(column=5, row=6)
        self.istTPValueLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.istTPValueLabel.grid(column=6, row=6)
        self.istTPUnit = tk.Label(self, text="%", font='Helvetica 14')
        self.istTPUnit.grid(column=7, row=6)

        self.spuehlenLabel = tk.Label(self, text="Argon Durchfluss", font='Helvetica 14')
        self.spuehlenLabel.grid(column=5, row=7)
        self.spuehlenRateLabel = tk.Label(self, text=str(-1), fg='blue', font='Helvetica 14')
        self.spuehlenRateLabel.grid(column=6, row=7)
        self.spuehlenUnit = tk.Label(self, text="%", font='Helvetica 14')
        self.spuehlenUnit.grid(column=7, row=7)
        # ---------------------------------------------------------
        self.seperatorLabel1 = tk.Label(self, text="----------------", font='Helvetica 14')
        self.seperatorLabel1.grid(column=1, row=5)
        self.seperatorLabel2 = tk.Label(self, text="---------", font='Helvetica 14')
        self.seperatorLabel2.grid(column=2, row=5)
        self.seperatorLabel3 = tk.Label(self, text="---------", font='Helvetica 14')
        self.seperatorLabel3.grid(column=3, row=5)

        self.separatorLabel4 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel4.grid(column=4, row=1)
        self.separatorLabel5 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel5.grid(column=4, row=2)
        self.separatorLabel6 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel6.grid(column=4, row=3)
        self.separatorLabel10 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel10.grid(column=4, row=4)
        self.separatorLabel11 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel11.grid(column=4, row=5)
        self.separatorLabel12 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel12.grid(column=4, row=6)
        self.separatorLabel12 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel12.grid(column=4, row=7)
        self.separatorLabel12 = tk.Label(self, text="|", font='Helvetica 14')
        self.separatorLabel12.grid(column=4, row=8)

        self.seperatorLabel7 = tk.Label(self, text="----------------", font='Helvetica 14')
        self.seperatorLabel7.grid(column=5, row=8)
        self.seperatorLabel8 = tk.Label(self, text="---------", font='Helvetica 14')
        self.seperatorLabel8.grid(column=6, row=8)
        self.seperatorLabel9 = tk.Label(self, text="---------", font='Helvetica 14')
        self.seperatorLabel9.grid(column=7, row=8)

        # ---------------------------------------------------------

        self.loggingBtn = tk.Button(self, bd=4, bg='#90EE90', text="Logging", command=toggle_log, font='Helvetica 14')
        self.loggingBtn.grid(column=1, row=8)

        self.loggingLabel = tk.Label(self, text="Inaktiv", fg='red', font='Helvetica 14')
        self.loggingLabel.grid(column=2, row=8)

        self.stateLabel = tk.Label(self, text="State", font='Helvetica 14')
        self.stateLabel.grid(column=1, row=10)

        self.stateLabelValue = tk.Label(self, text=str(state), fg='blue', font='Helvetica 14')
        self.stateLabelValue.grid(column=2, row=10)

        self.statusNotausLabel = tk.Label(self, text=str("Notaus"), font='Helvetica 14')
        self.statusNotausLabel.grid(column=1, row=9)

        self.statusNotausLabelValue = tk.Label(self, text=str(notaus), font='Helvetica 14')
        self.statusNotausLabelValue.grid(column=2, row=9)

        self.resetBtn = tk.Button(self, bd=4, bg='#90EE90', text="Reset", command=reset_notaus, font='Helvetica 14')
        self.resetBtn.grid(column=3, row=9)
        # ---------------------------------------------------------

        self.menubar = Menu(self)
        self.filemenu = Menu(self.menubar, tearoff=0, font=("", 24))
        self.filemenu.add_command(label="Exit", command=self.quit, font=("", 24))
        self.menubar.add_cascade(label="File", menu=self.filemenu, font=("", 24))

        self.helpmenu = Menu(self.menubar, tearoff=0, font=("", 24))
        self.helpmenu.add_command(label="Help Index", command=helpme, font=("", 24))
        self.helpmenu.add_command(label="About...", command=aboutme, font=("", 24))
        self.menubar.add_cascade(label="Help", menu=self.helpmenu, font=("", 24))

        self.config(menu=self.menubar)

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

        self.board.argonVentil.write(0)
        self.board.hochspannung.write(0)


app = MyApplication()
update()
app.mainloop()
