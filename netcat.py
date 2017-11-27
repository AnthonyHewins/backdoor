"""
Protocol

{
'cmd': {'e', 's', 'u'},
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
# Client code
#===============================================================================

def receive(connection):
	try:
		return loads(client.recv(1024 * 10))
	except EOFError as e:
		print("Connection closed")
	except OSError as e:
		print()

def upload_client(conn, upload):
	f = open(upload[0], 'br').read()
	obj = {
		'cmd':'u',
		'args':upload[1],
		'data':f
	}
	obj = dumps(obj)
	conn.send(obj)

def shell_client(conn, command):
	obj = None
	if command == 'e' or command == 'exit':
		conn.shutdown(socket.SHUT_RD)
		return False
	else:
		obj = {
			'cmd':'s',
			'data':command
		}
	conn.send(dumps(obj))
	return True
	
def client_loop(addr, upload, shell):
	conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	conn.connect((addr[0], addr[1]))
	if upload is not None:
		upload_client(conn, upload)
	while shell:
		continuing = shell_client(conn, input("#> "))
		if not continuing:
			break
		print(conn.recv(1024).decode('utf-8'))
	conn.close()

#===============================================================================
# Server code
#===============================================================================

def upload_server(data):
	try:
		f = open(data['args'], 'bw')
		f.write(data['data'])
		f.close()
		return True
	except:
		return False

def shell_server(command):
	command = command.rstrip() # when you hit enter there's a linefeed, this deletes it
	output = None
	try:
		output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
	except:
		output = "Failed the command"
	return output
	
def server_loop(addr):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((addr[0], addr[1]))
	server.listen(1)
	client, caddr = server.accept()

	while True:
		data = loads(client.recv(1024 * 10))

		if not data:
			client.shutdown()
			client.close()
			break
		
		if data['cmd'] == 'u':
			success = upload_server(data)
			if not success:
				client.send(b'Failed uploading the file, closing connection')
				client.close()
				return
			else:
				client.send(b'Successfully uploaded file')
		elif data['cmd'] == 's':
			output = shell_server(data['data'])
			client.send(output)
		else:
			client.close()
					
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
		print('Your port is invalid. Here is the exact exception:')
		print(e)
		exit()

	if args.role == 's':
		server_loop(addr)
	else:
		client_loop(addr, args.upload, args.shell)
