vim9script noclear
# vim global plugin for rich presence on discord
# maintainer: rufus193 <rufus09173@gmail.com>
if exists("g:loaded_richpresence")
	finish
endif
g:loaded_richpresence = 1

#prepare for talking to discord
var plugin_dir = expand("<sfile>:p:h:h")
function g:Init_rich_presence()
	let pid = getpid()
	python3 << EOF

#====== initialise python ======#
from sys import path
import vim
import time
import os
import uuid
from datetime import datetime


python_root = f"{vim.eval('s:plugin_dir')}/python" #get to the python dir to import module
path.insert(0,python_root) #allows module importing

#hide your name from the path
import getpass
def redact_path(path):
	return path.replace(f"/{getpass.getuser()}/","/[user]/")

#====== initialise discord rpc ======#
from rpc import DiscordRPC

#initialise an RPC connection
try:
	discord_rpc = DiscordRPC("439476230543245312",timeout=0.5) #1s timeout to not keep the user waiting
except (TimeoutError,ConnectionRefusedError):
	vim.command('echo "failed to initialise discord rich presence"')
	discord_rpc = None
except FileNotFoundError:
	vim.command('echo "discord rich presence not available"')
	discord_rpc = None

EOF
endfunction

#refresh the prersence
function g:Set_presence()
	let filename = expand("%:p")
	let filetype = &ft
	if len(filename) == 0
		let filename = "New file"
	endif
	if len(filetype) == 0
		let filetype = "Text"
	endif
	python3 << EOF

#is rich presence setup
if discord_rpc:
	#activity details
	activity = {
		"details": f"Editing {vim.eval("filename")}",
		"state": f"Type: {vim.eval("filetype")}",
		"type": 5, #competing
		"instance": True,
		"timestamps": {
			"start": int(datetime.now().timestamp())
		},
	}

	#prep new rich presence data
	data = {
		"cmd": "SET_ACTIVITY",
		"args": {
			"pid": os.getpid(),
			"activity": activity,
		},
		"nonce": str(uuid.uuid4()),
	}
	discord_rpc.send(data)

EOF
endfunction

function g:Stop_presence()
	python3 << EOF
if discord_rpc:
	#hopefully clear rich pre
	data = {
		"cmd": "SET_ACTIVITY",
		"args": {
			"pid": os.getpid(),
			"activity": None,
		},
		"nonce": str(uuid.uuid4()),
	}
	discord_rpc.send(data)
EOF
	python3 [discord_rpc.close() if discord_rpc != None else None]
	python3 discord_rpc = None
endfunction

function g:Rich_presence_full_start()
	call Init_rich_presence()
	call Set_presence()
endfunction

#commands
command Initpresence call Init_rich_presence()
command Setpresence call Set_presence()
command Stoppresence call Stop_presence()
command Startpresence call Rich_presence_full_start()

#autocommand to run the stuff
augroup RichPresence
	autocmd!
	autocmd VimEnter * call Rich_presence_full_start()
	autocmd VimLeave * call Stop_presence()
augroup END

finish
