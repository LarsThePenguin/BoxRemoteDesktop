########################
#   BoxRemoteDesktop   #
# By: Lars the Penguin #
########################

# Visit the computers IP address

from websocket_server import WebsocketServer
from PIL import ImageGrab
import http.server
import pyautogui
import threading
import base64
import socket

pyautogui.FAILSAFE = False
scaleDownMultiplier = 1.5

pswd = "1234"
ENABLEPASSWORD = False

IPADDRESS = socket.getfromhostname(socket.gethostname())
HTTPport = 80

print(f"Hosting on {IPADDRESS} at port {HTTPport} (HTTP) and 1048 (Websocket)")
if ENABLEPASSWORD == True:
	print("WARNING: You enabled password authentication, which uses the Javascript 'prompt()' function, which might not work properly on most browsers!")

class HTTPserver(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.wfile.write(b"""
<!DOCTYPE html>
<html><head>
    <title>Box Engine Project Remote Desktop</title>

    <meta charset="utf-8">
    <meta http-equiv="Content-type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>

<body>
<div>
	<img id="screen" onclick="leftclick(event)" oncontextmenu="rightclick(event)"></img>
	<br/>
	<input type="checkbox" id="allscreens" name="allscreens">
	<label for="allscreens"> Get all screens (Mouse controls are kind of broken though)</label>&emsp;&emsp;
	<button id="disconnect" onclick="disconnect()">Disconnect</button>
	<script>
		let pswd = """+(b"prompt('Enter Password')" if ENABLEPASSWORD else b"1234")+b"""
		const socket = new WebSocket("ws://"""+bytes(IPADDRESS, "utf-8")+b""":1048");
		window.onload = function(){
    	window.onkeydown= function(gfg){ 
			socket.send("Key:"+gfg.keyCode.toString())
    	};  
		};
		socket.onmessage = (event) => {
		  document.getElementById("screen").src = "data:image/png;base64, ".concat(event.data)
		};
		function FPS() {
			if (document.getElementById('allscreens').checked) {
		    	socket.send("Screen:1"+":"+pswd)
			} else {
				socket.send("Screen:0"+":"+pswd)
			}
		}
		function leftclick(event) {
			socket.send("Mouse:"+event.clientX.toString()+":"+event.clientY.toString()+":0"+":"+pswd)
		}
		function rightclick(event) {
			socket.send("Mouse:"+event.clientX.toString()+":"+event.clientY.toString()+":1"+":"+pswd)
		}
		function disconnect() {
			socket.close()
		}

		setInterval(FPS, 1000/"""+bytes(self.path.replace("/", ""), encoding="utf-8")+b""");
	</script>
</div>

<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
</body></html>""")

def CaptureWindow(allScreens):
	img = ImageGrab.grab(all_screens=allScreens)
	img = img.resize((int(img.width/scaleDownMultiplier), int(img.height/scaleDownMultiplier)))
	img.save("tmp.jpg")
	with open("tmp.jpg", "rb") as f:
		data = f.read()
		return base64.b64encode(data)

def handleWebsocketMessageReceived(client, server, message):
	if message.split(":")[-1] == pswd or not ENABLEPASSWORD:
		if message.split(":")[0] != "Screen":
			if message.split(":")[0] == "Key":
				pyautogui.typewrite(chr(int(message.split(":")[1])))
			if message.split(":")[0] == "Mouse":
				pyautogui.moveTo(int(int(message.split(":")[1])*scaleDownMultiplier), int(int(message.split(":")[2])*scaleDownMultiplier))
				if message.split(":")[3] == "0":pyautogui.leftClick()
				if message.split(":")[3] == "1":pyautogui.rightClick()
		if message.split(":")[0] == "Screen":
			if message.split(":")[1] == "1":
				server.send_message(client, CaptureWindow(True))
			if message.split(":")[1] == "0":
				server.send_message(client, CaptureWindow(False))

def WebsocketThread():
	server = WebsocketServer(host=IPADDRESS, port=1048)
	server.set_fn_message_received(handleWebsocketMessageReceived)
	server.run_forever()

def HTTPserverThread():
	webServer = http.server.HTTPServer((IPADDRESS, 80), HTTPserver)

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")

threading.Thread(target=HTTPserverThread).start()
WebsocketThread()
