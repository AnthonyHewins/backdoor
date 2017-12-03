"""
Protocol
Client->Server := {
    'cmd': {'e', 's', 'u'},
    'args': *,
    'data': *
}

Server->Client := {
    'cmd': {'200', '500'}
    'args': *,
    'data': *
}
"""
from os import system as cmd
import sys
import socket
from pickle import dumps, loads
from threading import Thread
import subprocess

#===============================================================================
# Shared methods
#===============================================================================
def shutdown():
	try:
		conn.shutdown(socket.SHUT_RDWR)
		conn.close()
	except OSError:
		pass
	except Exception as e:
		print("Failure closing socket:\n" + str(e))
	exit()


def receive():
	try:
		return loads(conn.recv(1024 * 10))
	except EOFError as e:
		print('Input killed')
		shutdown()
		
def send(data):
	try:
		conn.send(dumps(data))
	except Exception as e:
		print(e)
		shutdown()

#===============================================================================
# Client code
#===============================================================================
def ack():
	response = receive()
	print(response['data'])

def upload_client(upload):
	try:
		f = open(upload[0], 'br').read()
	except:
		print("Error: file could not be opened")
		return
	
	obj = {
		'cmd':'u',
		'args':upload[1],
		'data':f
	}
	send(obj)
	ack()

def shell_client():
	command = input("#> ")
	if command == 'e' or command == 'exit':
		shutdown()
	obj = {
		'cmd':'s',
		'data':command
	}
	send(obj)
	ack()
	
def client_loop(addr, upload, shell):
	global conn
	conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	conn.connect((addr[0], addr[1]))
	
	if upload is not None:
		upload_client(upload)

	while shell:
		shell_client()
		
	shutdown()

#===============================================================================
# Server code
#===============================================================================

def upload_server(data):
	obj = None
	try:
		f = open(data['args'], 'bw')
		f.write(data['data'])
		f.close()

		obj = {
			'cmd':'200',
			'data':'Wrote ' + data['args'] + ' successfully'
		}
	except Exception as e:
		obj = {
			'cmd':'500',
			'data':'Error writing ' + data['args'] + ':\n' + str(e)
		}
		
	send(obj)
		
def shell_server(command):
	command = command.rstrip() # when you hit enter there's a linefeed, this deletes it
	output = None

	obj = None
	try:
		output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True).decode('utf-8')
	except:
		output = "Failed the command at the python level"
	obj = {
		'cmd':'201',
		'data':output
	}
	send(obj)

def server_loop(addr):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((addr[0], addr[1]))
	server.listen(1)

	global conn
	conn, caddr = server.accept()

	while True:
		request = receive()

		if request is None:
			break
		
		if request['cmd'] == 'u':
			upload_server(request)
		elif request['cmd'] == 's':
			shell_server(request['data'])
		else:
			print(request)
			send({'cmd':'500', 'data':'This command is not implemented'})
	
	shutdown()
			
#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Python netcat. Drop files, download files, execute, and sniff.")
	parser.add_argument('role', type=str, help='Pick if you serve or are the client', choices=['c', 's'])
	parser.add_argument('target', type=str, help='IP and port you want to target (IP:port)', default='0.0.0.0:2222')
	parser.add_argument('-s', '--shell', action='store_true', help="Open a shell")
	parser.add_argument('-u', '--upload', nargs=2, type=str, help='On receive, put the file located locally at argv[0] in the specified destination argv[1] on the server')
	args = parser.parse_args()

	addr = args.target.split(':')
	try:
		addr[1] = int(addr[1])
	except Exception as e:
		print('Your port is invalid. Defaulting to 2222.')
		addr[1] = 2222

	if args.role == 's':
		server_loop(addr)
	else:
		if args.upload is None:
			args.shell = True
		client_loop(addr, args.upload, args.shell)
