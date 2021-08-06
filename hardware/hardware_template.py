import random

####################################################### start MQTT section ###########################################################################
from paho.mqtt import client as mqtt_client

#################  start MQTT config ####################
broker      = 'broker.emqx.io'
port        = 1883
client_id   = "123"
username    = 'emqx'
password    = 'public'
#################  end MQTT config ####################

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

    result = client.publish("/helloBroker", "{}".format(client_id))
#################  start subscribe topic ####################
    client.subscribe("/client/{}".format(client_id))

#################  end subscribe topic ####################


def on_message(client, userdata, msg):
#################  start process subscribed topic ####################
    print(msg.topic+" "+str(msg.payload))

#################  end process subscribed topic ####################


def connect_mqtt():
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    return client

####################################################### end MQTT section ###########################################################################

def main():
    global client
    count_HB = 0
    client = connect_mqtt()

    #client.loop_forever()
    client.loop_start() #use this if you have logic behind

    while(1):
        client.publish("{}/HB".format(client_id), count_HB)
        print("send heart beat {}".format(count_HB))
        count_HB = count_HB + 1
        sleep(5)

if __name__ == "__main__":
    main()