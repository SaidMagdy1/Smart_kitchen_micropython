#***************************************
#** by    :   Mohammed Rashad         **
#**           Abdelmonuiem Bahaa      **
#**           Mohammed zaky           **
#**           Saed magdy              **
#**           Mohammed Roshdy         **
#**                                   **
#** date  :   6 Jan 2021              **
#** Title :   Smart Kitchen v7.0      **
#***************************************
#***************************************


#modules and libraries 
#***************************************
from machine import Pin, ADC, PWM
import machine, onewire, ds18x20, time
import network
#***************************************


#wifi initialization as Access point interface
#***************************************
ssid     = 'Smart Kitchen'
password = '123456789'
ap       = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password)
while not ap.active():
    pass
print('network config:', ap.ifconfig())
#***************************************



# Configure the socket connection
# over TCP/IP
#***************************************
import socket
# AF_INET - use Internet Protocol v4 addresses
# SOCK_STREAM means that it is a TCP socket.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('',80)) # specifies that the socket is reachable by any address the machine happens to have
s.listen(5)     # max of 5 socket connections
#***************************************



#function for controlling servo by angle:
#***************************************
def map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
#***************************************
    
 
#gas sensor setup:
mq2    = ADC(Pin(34))
mq2.atten(ADC.ATTN_11DB)
#ds_pin setup:
ds_pin = Pin(4)
#beeper setup
beeper = PWM(Pin(21),freq = 5 ,duty = 512)
time.sleep(0.5)
beeper.duty(0)
#servo setup:
p23    = machine.Pin(23)
servo  = machine.PWM(p23,freq=50)

#requesting maximum temperatue , maximum gas conc. and mode :
#***************************************
conn, addr = s.accept()
print("Got connection from %s" % str(addr))
request    = conn.recv(1024)
print("")
print("Content %s" % str(request))
request    = str(request)
max_temp   = int(request[2:5])
max_gs     = int(request[5:8])
mode       = request[8]
#***************************************


#enable manual mode or continue auto
#***************************************
if mode    =='m': 
  conn.close()
else:
  pass
#***************************************


#opening the tap(first 20 degree for self ignition then the requested angle):
servo.duty(map(20,0,180,20,120))
time.sleep(2)
servo.duty(map(90,0,180,20,120))
#ds object to communicate with onewire protocol 
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
#scan for ds_sensor
roms = ds_sensor.scan()


while True:
  #check if (Gas off) button is pressed or not **works only in manual mode**
  #***************************************  
  s.settimeout(0.5)  #to make the connection non-blocking
  try:
    conn, addr  = s.accept()
    data        = conn.recv(100)
    data        = str(data)
    if data[2:5]=='off':
      servo.freq(50)
      servo.duty(map(0,0,180,20,120))
      time.sleep(0.1)
      break

  except:
    pass
  #***************************************
  
  
  #get sampled temperature
  ds_sensor.convert_temp()
  #delay for converting temperature
  time.sleep_ms(750)
  #rom takes an address from the list roms 
  for rom in roms:
    #variable for  the read temperature
    #***************************************
    temp_now= ds_sensor.read_temp(rom)
    print("Temperature:",temp_now)
    #***************************************
   
    #variable for the read gas conc
    #***************************************
    mq2_value = mq2.read()/4
    print("Gas conc:",mq2_value)
    #***************************************
    
    
    
    #detecting if max temp reached
    #***************************************
    if temp_now> max_temp:
        print("Max temperature reached")
        #closing the tap
        servo.freq(50)
        servo.duty(map(0,0,180,20,120))
        time.sleep(0.1)
        #send notification to app
        conn.send("Max Temprature reached".encode("utf-8"))
        #alarm to notify 
        beeper = PWM(Pin(21),freq = 5 ,duty = 512)
        time.sleep(3)
        beeper.deinit()
        break
    #***************************************
    
    #detecting if there is a gas leakage
    #***************************************
    if mq2_value> max_gs:
        print("gas leakage detected")
        servo.freq(50)
        servo.duty(map(0,0,180,20,120))
        time.sleep(0.1)
        #send notification to app
        conn.send("Max Gas concentration reached".encode("utf-8"))
        #alarm to notify
        beeper = PWM(Pin(21),freq = 5 ,duty = 512)
        time.sleep(3)
        beeper.deinit()
        break
    #***************************************
    time.sleep(1)
    
  #app end
  #***************************************
  if temp_now>max_temp or mq2_value > max_gs:
      print("Thanks for using me")
      break
  #***************************************
    
     

