import time


def get_bytes(t, iface='eth1'):
    with open('/sys/class/net/' + iface + '/statistics/' + t + '_bytes', 'r') as f:
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

    print("TX: {}Mbps  RX: {}Mbps".format(tx_speed, rx_speed))

    return {
                "TX": tx_speed,
                "RX": rx_speed
            }

init_network_status()

while(True):
    time.sleep(1)
    status = get_network_status()

    print("TX: {}Mbps  RX: {}Mbps".format(status['TX'], status['RX']))