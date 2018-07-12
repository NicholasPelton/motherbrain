from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(29,GPIO.OUT)
GPIO.output(29,GPIO.HIGH)

#def create_app():
app = Flask(__name__)  
Bootstrap(app)

#    return app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ledon', methods =['POST'])
def ledon():
    if GPIO.input(29):GPIO.output(29,GPIO.LOW)
    else:GPIO.output(29,GPIO.HIGH)
    return ('', 204)

if __name__ == '__main__':
    app.run(debug = "true", host='0.0.0.0')


GPIO.cleanup()
