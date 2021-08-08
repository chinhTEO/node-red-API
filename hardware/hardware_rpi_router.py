from threading import Thread
import threading
import psutil

##################################################### NETWORk #################################################################
import time

def get_bytes(t, iface='eth1'):
    with open('/sys/class/net/' + iface + '/statistics/' + t + '_bytes', 'r') as f:
        data = f.read()
        return int(data)

def get_link_speed(iface='eth1'):
    with open('/sys/class/net/' + iface + '/speed', 'r') as f:
        data = f.read()
        return int(data)

def init_network_status(iface='eth1'):
    global last_time
    global last_tx
    global last_rx

    last_time = time.time()
    last_tx = get_bytes('tx',iface)
    last_rx = get_bytes('rx',iface)

def get_network_status(iface='eth1'):
    global last_time
    global last_tx
    global last_rx

    period = time.time() - last_time 
    last_time = time.time()

    tx = get_bytes('tx',iface)
    rx = get_bytes('rx',iface)

    tx_speed = round((tx - last_tx)/(125000*period), 2)
    rx_speed = round((rx - last_rx)/(125000*period), 2)

    last_tx = tx
    last_rx = rx

    tx_bandwidth = get_link_speed('eth0')
    rx_bandwidth = get_link_speed('eth1')

    return {
                "TX"            : tx_speed,
                "RX"            : rx_speed,
                "TX_link_speed" : tx_bandwidth,
                "RX_link_speed" : rx_bandwidth
            }

##################################################### LED CONFIG ############################################################
LED_PIN_RED         = 26
LED_PIN_GREEN       = 13
LED_PIN_YELLO       = 19

####################################################### start MQTT section ###########################################################################
from paho.mqtt import client as mqtt_client
import json

#################  start MQTT config ####################
broker = "192.168.1.191"
port = 1883
client_id = "236"
username = 'emqx'
password = 'public'
#################  end MQTT config ####################

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        #print(("Connected to MQTT Broker!")
        pass
    else:
        #print(("Failed to connect, return code %d\n", rc)
        pass

    result = client.publish("/helloBroker", "{}".format(client_id))
#################  start subscribe topic ####################
    client.subscribe("/client/{}".format(client_id))
    client.subscribe("/{}/cmd".format(client_id))
    #print(("/{}/cmd".format(client_id))

#################  end subscribe topic ####################

def getdiff(line_1, line_2):
    diff = []
    last_pos = 0
    context = ""
    #print(("line 1: {}".format(line_1))
    #print(("line 2: {}".format(line_2))
    for i in range(20):
        if line_1[i] == line_2[i]:
            if(last_pos != i):
                diff.append({'pos':last_pos,
                             'context':context})
                context = ""
                last_pos = i
            last_pos = last_pos + 1
        else:
            context = context + line_2[i]
            if(i == 20 - 1):
                diff.append({'pos':last_pos,
                             'context':context})

    return diff


def updateLCD(line, context):
    diffs = getdiff(LCD_context[line],context.ljust(20))
    for diff in diffs:
        lcd.cursor_pos = (line, diff['pos'])
        lcd.write_string(diff['context'])
    LCD_context[line] = context.ljust(20)


def on_message(client, userdata, msg):
#################  start process subscribed topic ####################
    #print((msg.topic+" "+str(msg.payload))
    requests = json.loads(msg.payload)
    for request in requests:
        if request['cmd'] == "set LED green":
            if request['state']:
                GPIO.output(LED_PIN_GREEN,GPIO.HIGH)
            else:
                GPIO.output(LED_PIN_GREEN,GPIO.LOW)

        if request['cmd'] == "set LED red":
            if request['state']:
                GPIO.output(LED_PIN_RED,GPIO.HIGH)
            else:
                GPIO.output(LED_PIN_RED,GPIO.LOW)

        if request['cmd'] == "set LED yello":
            if request['state']:
                GPIO.output(LED_PIN_YELLO,GPIO.HIGH)
            else:
                GPIO.output(LED_PIN_YELLO,GPIO.LOW)

        if request['cmd'] == "write line":
            updateLCD(request['line'],request['context'])
        
        if request['cmd'] == "clear LCD":
            #print(("clear LCD")
            lcd.clear()

        if request['cmd'] == "set LCD":
            lcd.backlight_enabled = request['state']

#################  end process subscribed topic ####################

def connect_mqtt():
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    return client

####################################################### end MQTT section ###########################################################################

################################################### LCD config ##############################################################
from RPLCD.i2c import CharLCD
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A02',
              auto_linebreaks=True,
              backlight_enabled=True)

################################################### ENCODER start ##########################################################
import RPi.GPIO as GPIO
from time import sleep


ENCODER_PIN_BUTTON  = 24
ENCODER_PIN_CLK     = 23
ENCODER_PIN_DIR     = 22

def rotationDecodeHandler(channel):
    sleep(0.002)
    Switch_A = GPIO.input(ENCODER_PIN_CLK)
    Switch_B = GPIO.input(ENCODER_PIN_DIR)
 
    if (Switch_A == Switch_B):
        client.publish("/{}/encoder".format(client_id), "1")
        #print(("encoder + 1")
    else:
        client.publish("/{}/encoder".format(client_id), "-1")
        #print(("encoder - 1")


def encoderButtonHandler(channel):
    client.publish("/{}/encoder".format(client_id), "0")
    #print(("encoder pressed")

def init_GPIO():
    #print(("init GPIO")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(ENCODER_PIN_BUTTON, GPIO.IN)
    GPIO.setup(ENCODER_PIN_CLK, GPIO.IN)
    GPIO.setup(ENCODER_PIN_DIR, GPIO.IN)

    GPIO.setup(LED_PIN_RED, GPIO.OUT)
    GPIO.setup(LED_PIN_GREEN, GPIO.OUT)
    GPIO.setup(LED_PIN_YELLO, GPIO.OUT)

    GPIO.add_event_detect(ENCODER_PIN_BUTTON, GPIO.RISING, callback=encoderButtonHandler, bouncetime=10)
    GPIO.add_event_detect(ENCODER_PIN_CLK, GPIO.RISING, callback=rotationDecodeHandler, bouncetime=10)

def send_heartbeat():
    global count_HB
    count_HB = 0
    while(1):
        HB_msg = {
            "ID":   client_id,
            "description" : "home router hardware",
            "beat": count_HB
        }
        client.publish("heartbeat".format(client_id), json.dumps(HB_msg))
        #print(("send heart beat {}".format(count_HB))
        count_HB = count_HB + 1
        sleep(5)

def send_networkStatus():
    init_network_status()
    while(1):
        status = get_network_status()
        client.publish("/{}/networkI0".format(client_id), json.dumps(status))
        #print(("send network IO {}".format(status))

        cpu_freq = psutil.cpu_freq()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        router_info = {
            "cpu_freq" : cpu_freq.current,
            "cpu_load" : cpu_percent,
            "memory_percent" : memory.percent 
        }
        client.publish("/{}/performance".format(client_id), json.dumps(router_info))
        #print(("send router info {}".format(router_info))

        sleep(1)

def main():
    global client
    global lcd
    global LCD_context
    client = connect_mqtt()
    init_GPIO()

    LCD_context = ["                    ","                    ","                    ","                    "]
    lcd.clear()

    #client.loop_forever()
    client.loop_start() #use this if you have logic behind

    t1 = threading.Thread(target=send_heartbeat)
    t2 = threading.Thread(target=send_networkStatus)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()