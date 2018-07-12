from flask import Flask, render_template, request, jsonify, Request
from wireless import Wireless
from picamera import PiCamera
from time import sleep
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import BaseJobStore
from apscheduler.triggers.interval import IntervalTrigger
import picamera
import Outlets
import usbtemper
import socket
import os
import time
import datetime

#create some globals for wireless stuff and outlet to pass outletname
wiredin = Wireless()
global jinjavar
global outlet
global temp
global hum

temp = usbtemper.findtemp()
hum = usbtemper.findhum()

#find wlan0 output link for wireless access
def wlan():
    if wiredin.current()!=None:
        gw = os.popen("ip -4 route show default").read().split()    
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
        s.connect((gw[2], 0))
        ipaddr = s.getsockname()[0]
        return str("url: " + ipaddr + ":5000")
    else:
        return str("None")

#Find the correct wifi icon
def ifwifi():
    if wiredin.current()!=None:
        return str("wifi")
    else:
        return str("wifi_off")

def do_nothing():
    return null

#All the crazy ways I have to derive the name of the outles from the json
def oselect(num):
    if num == 1: return outlet1
    elif num == 2: return outlet2
    elif num == 3: return outlet3
    elif num == 4: return outlet4
    elif num == 5: return led


#The spiffies make sure each completed job is replaced with the next
def spiffyon(outy):
    outy.on()
    if outy.url == "/feeding":
        if led.name == "NONE":
            outy.feeding()
            jobomatic()
        else:
            outy.feeding(led.t_on, led.t_off)
            jobomatic()
            
    print ("spiffy on activated!")
    print (outy.num)
    print (datetime.datetime.now())
    print (outy.check)

def spiffyoff(outy):
    outy.off()
    if outy.url == "/feeding":
        if led.name == "NONE":
            outy.feeding()
            jobomatic()
        else:
            outy.feeding(led.t_on, led.t_off)
            jobomatic()
    print ("spiffy off activated!")
    print (outy.num)
    print (datetime.datetime.now())
    print (outy.check)

#Check humidity and temperature and update necessary outlets
def checker():
    global temp
    global hum
    temp = usbtemper.findtemp()
    hum = usbtemper.findhum()
    for x in range(1,6):
        mustard = oselect(x)
        mustard.update(temp,hum,led.check())

#Use the camera!
def camerago():
    timenow = datetime.datetime.now()
    camera=PiCamera()
    camera.start_preview()
    time.sleep(3)
    camera.capture('/home/honky/server/static/pics/garden' + str(timenow.minute) + '.jpg')
    camera.stop_preview()
    camera.close()

#Set up outlet objects
led = Outlets.Outlet(29,"secondary",5, "NONE")
outlet1 = Outlets.Outlet(37, "danger",1, "NONE")
outlet2 = Outlets.Outlet(35, "success",2, "NONE")
outlet3 = Outlets.Outlet(33, "info",3, "NONE")
outlet4 = Outlets.Outlet(31, "warning",4, "NONE")

#create dictionary to save from rewriting every variable for jinja
jinjavar = dict(wificon=ifwifi(), webadr=wlan())

#def create_app():
app = Flask(__name__)  
#    return app

@app.route('/wireless') #Log on to Wireless!
def wireless():
    name = request.args.get('name', 0, type=str)
    password = request.args.get('password', 0, type=str)
    if wiredin.connect(ssid=name, password=password):wificon="wifi"
    else:wificon="wifi_off"
    return jsonify(result=wificon)

@app.route('/website') #Pause to return wifi web address
def website():
    global jinjavar
    if wiredin.current():time.sleep(6)
    jinjavar = dict(wificon=ifwifi(), webadr=wlan())
    return jsonify(result=wlan())

@app.route('/_set_template') #Set global outlet variable to correct Outlet
def _set_template():
    global outlet
    switch = request.args.get('switch', 0, type=int)
    outlet = oselect(switch)
    return jsonify(result=outlet.phrase())

@app.route('/_switch_board') #Turn outles off or on
def _switch_board():
    global outlet
    switch = request.args.get('switch', 0, type=int)
    outlet = oselect(switch)
    outlet.toggle()
    return jsonify(result=outlet.phrase())

@app.route('/')
def index():
    global wificon
    if wiredin.current()!=None:wificon = "wifi"
    else:wificon="wifi_off"
    temp = usbtemper.findtemp()
    hum = usbtemper.findhum()
    return render_template('index.html', led = led, outlet1 = outlet1, outlet2 = outlet2, outlet3 = outlet3, outlet4 = outlet4, temp = temp, hum = hum, **jinjavar)

@app.route('/garden')
def garden():
    #camera stuff, we'll fix later!
    temp = usbtemper.findtemp()
    hum = usbtemper.findhum()
    return render_template('garden.html', temp = temp, hum = hum, **jinjavar) 

#Specific routes for each outlet, mainly to set global outlet. LED has a different template.
@app.route('/sun')
def sun():
    global outlet
    outlet = led
    return render_template('sun.html', outlet = led, **jinjavar)

@app.route('/plug1')
def plug1():
    global outlet
    outlet = outlet1
    return render_template('outlet.html', outlet = outlet1, **jinjavar)

@app.route('/plug2')
def plug2():
    global outlet
    outlet = outlet2
    return render_template('outlet.html', outlet = outlet2, **jinjavar)

@app.route('/plug3')
def plug3():
    global outlet
    outlet = outlet3
    return render_template('outlet.html', outlet = outlet3, **jinjavar)

@app.route('/plug4')
def plug4():
    global outlet
    outlet = outlet4
    return render_template('outlet.html', outlet = outlet4, **jinjavar)


#Basic On/Off and Sunrise/Sunset and updates
@app.route('/daynight')
def daynight():
    global outlet
    outlet.daynight()
    jobomatic()
    return render_template('day_night.html', outlet = outlet, **jinjavar)

@app.route('/basic')
def basic():
    global outlet
    outlet.basic()
    jobomatic()
    return render_template('basic_light.html', outlet = outlet)

@app.route('/basicupdate')
def basicupdate():
    global outlet
    timeonstr = request.args.get('timeon', 0, type=str)
    timeoffstr = request.args.get('timeoff', 0, type=str)
    outlet.t_on = Outlets.formater(timeonstr)
    outlet.t_off = Outlets.formater(timeoffstr)
    outlet.timeon = timeonstr
    outlet.timeoff = timeoffstr
    jobomatic()
    return ('',204)

#Seasonal and updates.
@app.route('/seasonal')
def seasonal():
    global outlet
    outlet.seasonal()
    return render_template('seasonal_light.html', outlet = outlet)

#Climate and updates and various templates
@app.route('/climate')
def climate():
    global outlet
    outlet.climate()
    return render_template('climate_control.html', outlet = outlet)

@app.route('/climateupdate')
def climateupdate():
    global outlet
    # specific outlet variables
    if request.args.get('day_t', 0, type=str):
        outlet.day_t = request.args.get('day_t', 0, type=str)
    if request.args.get('night_t', 0, type=str):
        outlet.night_t = request.args.get('night_t', 0, type=str)
    if request.args.get('c_style', 0, type=str):
        outlet.c_style = request.args.get('c_style', 0, type=str)
    # universal outlet variables
    if request.args.get('d_t_high', 0, type=str):
        Outlets.Outlet.d_t_high = request.args.get('d_t_high', 0, type=int)
    if request.args.get('d_t_low', 0, type=str):
        Outlets.Outlet.d_t_low = request.args.get('d_t_low', 0, type=int)
    if request.args.get('n_t_high', 0, type=str):
        Outlets.Outlet.n_t_high = request.args.get('n_t_high', 0, type=int)
    if request.args.get('n_t_low', 0, type=str):
        Outlets.Outlet.n_t_low = request.args.get('n_t_low', 0, type=int)
    if request.args.get('h_high', 0, type=str):
        Outlets.Outlet.h_high = request.args.get('h_high', 0, type=int)
    if request.args.get('h_low', 0, type=str):
        Outlets.Outlet.h_low = request.args.get('h_low', 0, type=int)
    return ('',204)

@app.route('/ac')
def ac():
    global outlet
    return render_template('ac.html', outlet = outlet)

@app.route('/heater')
def heater():
    global outlet
    return render_template('heater.html', outlet = outlet)

@app.route('/humidifier')
def humidifier():
    global outlet
    return render_template('humidifier.html', outlet = outlet)

@app.route('/deHumidifier')
def deHumidifier():
    global outlet
    return render_template('deHumidifier.html', outlet = outlet)

#Feeding and updates
@app.route('/feeding')
def feeding():
    global outlet
    return render_template('feeding_schedule.html', outlet = outlet, led = led)

@app.route('/feedingupdate')
def feedingupdate():
    global outlet
    if request.args.get('aday', 0, type=int):
        outlet.aday = request.args.get('aday', 0, type=int)
    if request.args.get('aday2', 0, type=int):
        outlet.aday2 = request.args.get('aday2', 0, type=int)
    if request.args.get('day_t', 0, type=str):
        outlet.day_t = request.args.get('day_t', 0, type=str)
    if led.name!="NONE" and outlet.day_t=="checked":
        outlet.feeding(led.t_on, led.t_off)
    else:
        outlet.feeding()
    jobomatic()
    return jsonify(aday = outlet.aday, aday2=outlet.aday2, feedon = outlet.feed_on_str)

#Return empty template and erase jobs
@app.route('/none')
def none():
    global outlet
    outlet.none()
    jobkiller()
    return ('',204)
    
    
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.start()

#Set up methods to start jobs, kill them, and create dummy jobs
    def jobkiller():
        global outlet
        scheduler.remove_job(str(outlet.num)+'on')
        scheduler.remove_job(str(outlet.num)+'off')
        scheduler.add_job(do_nothing, 'cron',hour=20,id=str(outlet.num)+'off')
        scheduler.add_job(do_nothing, 'cron',hour=20,id=str(outlet.num)+'on')

    def jobomatic():
        global outlet
        buggo = outlet #Use buggo to pass outlet instance instead of the ever changing global outlet
        scheduler.remove_job(str(outlet.num)+'on')
        scheduler.remove_job(str(outlet.num)+'off')
        scheduler.add_job(lambda: spiffyon(buggo), 'cron'
                          ,hour=outlet.t_on.hour
                          ,minute=outlet.t_on.minute
                          ,id=str(outlet.num)+'on')
        scheduler.add_job(lambda: spiffyoff(buggo), 'cron'
                          ,hour=outlet.t_off.hour
                          ,minute=outlet.t_off.minute
                          ,id=str(outlet.num)+'off')
    def jobdummystart():
        for x in range(1,6):
            scheduler.add_job(do_nothing, 'cron'
                          ,hour=20
                          ,id=str(x)+'off')
            scheduler.add_job(do_nothing, 'cron'
                          ,hour=8
                          ,id=str(x)+'on')
    #Set up dummy jobs so it doesn't complain
    #Set up interval based jobs
    jobdummystart()
    scheduler.add_job(checker,'interval', minutes=5)
    scheduler.add_job(camerago, 'cron',hour=12)
    app.run(debug = "False", host='0.0.0.0')


Outlets.cleanup()
