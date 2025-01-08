from flask import *
from base64 import b64decode, b64encode
from time import ctime, sleep, time
from threading import Thread
from datetime import datetime, timezone
import gzip, requests, json
from getFreeRoomsFromAde2 import AdeRequest
            
Ade = AdeRequest()
infos = Ade.getRoomsInfos()
global freeRooms
freeRooms = Ade.getCurrentsFreeRooms()



def import_allowed():
    global freeRooms
    tab = []
    
    for room in freeRooms:
        tab.append([room, freeRooms[room]["freeUntil"]])
    return tab

def import_response_data():
    global freeRooms
    tab = []
    
    for room in freeRooms:
        tab.append([room, freeRooms[room]["capacity"], freeRooms[room]["freeUntil"], freeRooms[room]["busy"]])
    return tab

app = Flask(__name__)
app.config['response_data'] = import_response_data() # [numRoom: str, capacity: int, freeUntil: str, busy: tuple]
app.config['allowed'] = import_allowed() # [numRoom: str, freeUtil: str]

def reloadData():
    global freeRooms
    while True:
        try:
            #sleep(600)
            if datetime.now().minute % 20 == 0:
                Ade = AdeRequest()
                infos = Ade.getRoomsInfos()
                freeRooms = Ade.getCurrentsFreeRooms()
                app.config['response_data'] = import_response_data() # [numRoom: str, capacity: int, freeUntil: str, busy: tuple]
                app.config['allowed'] = import_allowed() # [numRoom: str, freeUtil: str]
                print("[" + datetime.now().strftime("%y/%m/%d %H:%M:%S") + "] Refresh Data From Ade")
                sleep(120)
            sleep(10)
            
        except Exception as e:
            print("Err. When reload:", e)
            sleep(30)
            

Thread(target=reloadData).start()


@app.route('/')
def index():
    prepPage = ""
    deux = ""
    for ip in app.config["allowed"]:
        prepPage += "<div class=\"ip-item" + deux + "\" onclick=\"PrintResponse(this, '" + ip[0] +"');\">\n"
        ipPadded = ip[0] + ((14 - len(ip[0])) * "&nbsp;")
        prepPage += "<p>Salle n°" + ipPadded + "</p>&nbsp;\n"
        prepPage += "<p>Disponible jusqu'à -> " + ip[1] + "</p>&nbsp;\n"
        
        prepPage += "</div>\n"
        if deux == "":
            deux = "2"
        else:
            deux = ""
    
    res = open("templates/index.html", "r").read().replace("=====cnt=====", prepPage).replace("\\=====HOME-IP_Addr=====\\", "Get Free Rooms From Ade").encode()
    resp = Response(gzip.compress(res))
    resp.headers['Content-Encoding'] = 'gzip'
    return resp


@app.route("/responsesFrom/<ip>")
def responsesFrom(ip):
    def busyUntil(tab):
        ts, te = tab
        return f'- {str(ts[0]).zfill(2)}h{str(ts[1]).zfill(2)} à {str(te[0]).zfill(2)}h{str(te[1]).zfill(2)}\n'
    responses = "\r\n\r\n"
    for resp in app.config['response_data']:
        if resp[0] == ip:
            responses += str(ip) + "    capacité: " + str(resp[1]) + "    disponible jusqu'à: " + str(resp[2])
            if resp[3] != []:
                responses  += "\noccupée durant:\n" + str("".join(busyUntil(x) for x in resp[3])) + "\r\n\r\n"
    resp = Response(gzip.compress(responses.encode()))
    resp.headers['Content-Encoding'] = 'gzip'
    return resp

@app.route('/api')
def apiRooms():
    global freeRooms
    return json.dumps(freeRooms)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
