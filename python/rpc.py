import os
from socket import *
from pathlib import Path
import json

class DiscordRPC:
	def __init__(self,client_id,timeout = None):
		#rpc socket can live in any of these directories
		discord_socket_dirs = [
			os.environ[dir] for dir in ["XDG_RUNTIME_DIR","TMPDIR","TMP","TEMP"]
			if os.environ.get(dir) != None
		]
		discord_socket_dirs.append("/tmp")
		#====== find the socket ======#
		self.socket_path = None
		for dir in discord_socket_dirs:
			for file in Path(dir).iterdir():
				if file.name[:12] == "discord-ipc-":
					self.socket_path = file
		if self.socket_path == None:
			raise FileNotFoundError("Could not find discord RPC socket")
		#====== connect ======#
		self.socket = socket(AF_UNIX,SOCK_STREAM)
		self.socket.settimeout(timeout)
		self.socket.connect(str(self.socket_path))
		#====== handshake ======#
		self.send({"v": 1, "client_id": client_id},0)
		opcode, data = self.recv()
		if opcode != 1 or data["evt"] != "READY":
			raise RuntimeError("No handshake response received")
	
	def close(self):
		self.send({},2)
		self.socket.close()

	def send(self,data,opcode = 1):
		#json encode data if passed as a dictionary
		if type(data) == dict:
			data = json.dumps(data)
		#overflow protection
		if len(data) > 0xffffffff:
			raise OverflowError("data length would overflow")
		#header consists of 4 bytes of opcode followed by 4 bytes of length, then the data
		payload = b""
		payload += opcode.to_bytes(length=4,byteorder="little")
		payload += len(data).to_bytes(length=4,byteorder="little")
		payload += data.encode()
		self.socket.send(payload)

	def recv(self):
		#receive header
		header = self.socket.recv(8)
		opcode = int.from_bytes(header[:4],signed=False,byteorder="little") #first 4 bytes opcode
		length = int.from_bytes(header[4:],signed=False,byteorder="little") #second 4 bytes length
		#receive data
		data = self.socket.recv(length).decode()
		if len(data) == 0:
			raise ConnectionResetError("Connection was closed")
		return (opcode,json.loads(data))
