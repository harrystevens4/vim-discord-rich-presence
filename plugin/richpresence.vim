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
from sys import path
import vim
import time

python_root = f"{vim.eval('s:plugin_dir')}/python" #get to the python dir to import module
path.insert(0,python_root) #allows module importing

pid = int(vim.eval("pid"))

import discord_rich_presence

#use threaded version instead of this one
#discord = discord_rich_presence.discord_ipc(pid)
discord = discord_rich_presence.threaded_discord_rich_presence(pid)

#also obselete when threading
#discord.handshake() #so it is ready to get our data
EOF
endfunction

#refresh the prersence
function g:Set_presence()
	let filename = expand("%F")
	let filetype = &ft
	if len(filename) == 0
		let filename = "New file"
	endif
	if len(filetype) == 0
		let filetype = "Text"
	endif
	python3 discord.start_presence(f"Editing: {vim.eval('filename')}",f"Type: {vim.eval('filetype')}")
endfunction

#kill the socket
function g:Stop_presence()
	python3 discord.stop()
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
