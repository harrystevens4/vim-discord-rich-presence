#!/usr/bin/python3
import threading
import socket
import json
import struct
import os
import uuid
import sys
import time
class discord_ipc:
	def __init__(self,pid,discord_socket_path=None):
		self.start_time = int(time.time())
		self.pid = pid
		#find discords ipc socket
		discord_socket_locations = ["/var/run/user/1000/discord-ipc-0"]
		if discord_socket_path == None:
			for i in discord_socket_locations:
				if os.path.exists(i):
					discord_socket_path = i
		if discord_socket_path == None:
			return

		#connect to discords ipc
		try:
			self.sock = socket.socket(socket.AF_UNIX)
			self.sock.connect(discord_socket_path)
			self.sock.settimeout(1)
		except Exception as problem:
			print(problem)
			return
	def stop(self):
		try:
			self.send({},2)
			self.sock.close()
		except:
			pass

	def send(self,data,opcode = 1):
		try:
			data = json.dumps(data, separators=(",",":")).encode()
			header = struct.pack("<II",opcode,len(data))
	
			#print(f"h:{header}")
			self.sock.send(header)
			#print(f"b:{data}")
			self.sock.send(data)
		except:
			return -1

	def recv(self):
		try:
			#get response
			raw_header = self.sock.recv(8)
			op, header = struct.unpack("<II",raw_header)
			data = self.sock.recv(header).decode()
			data_json = json.loads(data)
			return data_json
		except:
			return -1

	def handshake(self):
		#prepare a handshake
		client_id = "439476230543245312" #vim bot
		#client_id = "887774122141167638" my bot
		handshake = {'v': 1, 'client_id': client_id}

		#handshake
		status = self.send(handshake,0)
		if status == -1:
			return -1
		#get hanshake response
		status = self.recv()
		if status == -1:
			return -1

	def set_presence(self,details="Editing a file",state="Type unknown"):
		#prepare activity
		activity = {
			"details":details,
			"state":state,
			"timestamps":{
				"start":self.start_time
			},
		}

		#prep new rich presence data
		data = {
			"cmd":"SET_ACTIVITY",#SET_ACTIVITY
			"args":{
				"pid": self.pid,#so discord knows when the "game" closes
				"activity":activity,
			},
			"nonce": str(uuid.uuid4()),
		}

		#send presence
		status = self.send(data)
		status = self.recv()
		if status == -1:
			return -1

class threaded_discord_rich_presence:
	def __init__(self,pid):
		self.discord = discord_ipc(pid)
	def wait_for_thread(self):
		while True:
			time.sleep(0.1)
			if self.done == True:
				return
	def start_presence_main_thread(self):
		self.discord.handshake()
		self.discord.set_presence(self.details,self.state)
		self.done = True
	def start_presence(self,details=None,state=None):
		self.details = details
		self.state = state
		self.ipc_thread = threading.Thread(target=self.start_presence_main_thread) 
		self.done = False
		self.ipc_thread.start()
	def stop(self):
		self.wait_for_thread()
		self.discord.stop()

if __name__ == "__main__":
	discord = threaded_discord_rich_presence(os.getpid())
	discord.start_presence()
	print("thread started")
	discord.wait_for_thread()
	print("thread done")
	while True:
		pass

	#discord = discord_ipc(os.getpid())
	#status = discord.handshake()
	#if status == -1:
	#	print("could not handshake")
	#while True:
	#	time.sleep(1)
	#	status = discord.set_presence()
	#	if status == -1:
	#		break
	#	print(status)
