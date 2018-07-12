import RPi.GPIO as GPIO
import time
import datetime

GPIO.setmode(GPIO.BOARD)

class Outlet():
    #universal climate setting variables n=night d=day t=temp h=humidity
    d_t_high = 90
    d_t_low = 70
    n_t_high = 70
    n_t_low = 60
    h_high = 60
    h_low = 40
    def __init__(self,port,color,num):
        #Starting Variables
        self.port = port
        self.color = color
        self.num = num
        self.name = "NONE"
        self.url = "/none"
        self.type = "No Setting"
        GPIO.setup(self.port,GPIO.OUT)
        GPIO.output(self.port,GPIO.HIGH)
        #Basic Variables
        self.t_on = datetime.time(4,0)
        self.t_off = datetime.time(22,0)
        self.timeon = "04:00"
        self.timeoff = "22:00"
        #Feeding Variables
        self.aday = 2
        self.aday2 = 3
        self.feed_on_str = []
        self.feed_on = []
        self.feed_off = []
        #Climate Variables
        self.c_style = "/ac"
        self.day_t = "checked"
        self.night_t = "checked"
    def check(self):
        if GPIO.input(self.port): return False
        else: return True
    def on(self):
        if self.check() == False:
            GPIO.output(self.port, GPIO.LOW)
            
    def off(self):
        if self.check():GPIO.output(self.port, GPIO.HIGH)
    def toggle(self):
        if self.check():self.off()
        else: self.on()
    def phrase(self):
        if self.num == 5:
            if self.check():return "wb_sunny"
            else: return "brightness_3"            
        else:
            if self.check():return "power"
            else: return "power_off"

    def daynight(self):
        if self.url!="/daynight":
            self.url = "/daynight"
            self.type = "Sunrise and Sunset"
            self.name = "SUN"
            self.day_t = "checked"

    def basic(self):
        if self.url!="/basic":
            self.url = "/basic"
            self.type = "Basic On/Off"
            self.name = "ON/OFF"

        self.t_on = formater(self.timeon)
        self.t_off = formater(self.timeoff)

    def seasonal(self):
        self.url = "/seasonal"
        self.type = "Seasonal Light"
        self.name = "SEASON"

    def climate(self):
        if self.url != "/climate":
            self.url = "/climate"
            self.type = "Climate Control"
            self.name = "CLIMATE"
            self.day_t = "checked"
            self.night_t = "checked"

    def update(self,temp,hum,ledstat):
        #Series of checks to see who needs to turn on or off due to hum/temp
        if self.name == "CLIMATE":
            if self.c_style == "/ac":
                if self.day_t == "checked":
                    if ledstat:
                        if temp > self.d_t_high:
                            self.on()
                        elif temp < self.d_t_low:
                            self.off()
                if self.night_t == "checked":
                    if ledstat==False:
                        if temp > self.n_t_high:
                            self.on()
                        elif temp < self.d_t_low:
                            self.off()
                            
            elif self.c_style == "/heater":
                if self.day_t == "checked":
                    if ledstat:
                        if temp > self.d_t_high:
                            self.off()
                        elif temp < self.d_t_low:
                            self.on()
                if self.night_t == "checked":
                    if ledstat==False:
                        if temp > self.n_t_high:
                            self.off()
                        elif temp < self.d_t_low:
                            self.on()
            elif self.c_style == "/humidifier":
                if hum < self.h_low:
                    self.on()
                if hum > self.h_high:
                    self.off()
            elif self.c_style == "/deHumidifier":
                if hum < self.h_low:
                    self.off()
                if hum > self.h_high:
                    self.on()

    def feeding(self, ledon=datetime.time(0,0), ledoff=datetime.time(23,59)):
        self.url = "/feeding"
        self.type = "Watering Schedule"
        self.name = "WATER"
        #Create lists for on and off times
        startfrom = time_to_min(ledon)
        if ledon < ledoff:
            span = time_to_min(ledoff) - time_to_min(ledon)
        else:
            span = 1400 - (time_to_min(ledon) - time_to_min(ledoff))
        duration = span/self.aday
        self.feed_on.clear()
        self.feed_off.clear()
        self.feed_on_str.clear()
        timenow = datetime.datetime.now().time()
        for x in range(self.aday):
            momenton = min_to_time(round(duration*x) + startfrom)
            momenton1 = momenton.strftime("%I:%M %p")
            momentoff = min_to_time(round(duration*x) + self.aday2 + startfrom)
            self.feed_on.append(momenton)
            self.feed_on_str.append(momenton1)
            self.feed_off.append(momentoff)

        #Sort lists so that they can be searched, the string list stays unordered
        self.feed_on.sort()
        self.feed_off.sort()

        self.t_on = datetime.time(0,0)
        for timeon in self.feed_on:
            if timeon > timenow:
                self.t_on = timeon
                break

        self.t_off = datetime.time(0,0)
        for timeoff in self.feed_off:
            if timeoff > timenow:
                self.t_off = timeoff
                break

    def none(self):
        self.url = "/none"
        self.type = "No Setting"
        self.name = "NONE"


#Other functions
def cleanup():
    GPIO.cleanup()

def formater(tim):
    if isinstance(tim,str):
        return datetime.datetime.strptime(tim, '%H:%M').time()
    else:
        return tim.strftime('%H:%M')

def min_to_time(minutes):
    hours = minutes//60
    minutes = minutes - hours*60
    if hours < 0: hours = hours*(-1)
    if hours > 23: hours = hours - 24
    time = datetime.time(hours,minutes)
    return time

def time_to_min(time):
    minutes = time.hour * 60 + time.minute
    return minutes

