import testinfra
import socket

class Mapper(object):
	__realname = None
	__connection = None
	__socketInfo = None
	__portMapping = None
	__filtering = ['raw','tnu','tcp','udp','unix']


	def __init__(self, host, username):
		self.host = host
		self.username = username
		self.__connection = testinfra.get_host('paramiko://{}@{}'.format(self.username,self.host))
		self.__realname = socket.gethostbyaddr(self.host)[0]
		self.__ipaddress = socket.gethostbyname(self.host)

	def __str__(self):
		return "{}(host = {}, username = {})".format(self.__class__.__name__,self.host,self.username)

	@property
	def sockInfo(self):
		return self.__socketInfo

	@property
	def clientInfo(self):
		return self.__portMapping

	@property
	def realname(self):
		return self.__realname

	@property
	def ipaddr(self):
		return self.__ipaddress


	def get_listening_sockets(self, filtering = None):
		if filtering is None:
			raise Exception("You need to specify a filter!")

		if not filtering in self.__filtering:
			raise Exception("Invalid filtering specified: <{}>! Valid filters are: <{}>".format(filtering,', '.join(self.__filtering)))			

		try:
			SocketInfo = self.__connection.socket.get_listening_sockets()
		except:
			raise Exception("Could not initialize testinfra connection to the host!") from None

		if filtering == 'raw':
			self.__socketInfo = SocketInfo
		elif filtering == 'tnu':
			self.__socketInfo = {'tcp':[],'udp':[]}

			for item in SocketInfo:
				if 'tcp:' in item or 'udp:' in item:
					root = 'tcp'
				else:
					rott = 'udp'
				prep = item.split('://')[1]
				if ':::' in prep:
					ip = 'ALL'
					port = prep.replace(':::','')
				else:
					ip = prep.split(':')[0]
					port = prep.split(':','')[1]

				self.__socketInfo[root].append({'IP':ip,'Port':port})
		elif filtering == 'tcp' or filtering == 'udp':
			if 'tcp' == filtering:
				root = 'tcp'
			else:
				root = 'udp'

			self.__socketInfo = {root:[]}

			for item in SocketInfo:
				if not root in item:
					continue

				prep = item.split('://')[1]
				if ':::' in prep:
					ip = 'ALL'
					port = prep.replace(':::','')
				else:
					ip = prep.split(':')[0]
					port = prep.split(':')[1]

				self.__socketInfo[root].append({'IP':ip,'Port':port})

		elif filtering == 'unix':
			self.__socketInfo = {'unix':[]}

			for item in SocketInfo:
				if 'unix' in item:
					self.__socketInfo['unix'].append(item.split('unix://')[1])

		return self.__socketInfo

	def get_clients(self, skiplocalhost = True, SkipIP = None):
		self.__portMapping = {}
		SocketInfo = self.get_listening_sockets(filtering = 'tcp')
		for connection in SocketInfo['tcp']:
			if not connection['Port']:
				continue
			for client in self.__connection.socket("tcp://" + connection["Port"]).clients:
				if client[0] == '127.0.0.1' and skiplocalhost:
					continue

				if client[0] == self.__ipaddress:
					continue

				if not SkipIP is None:
					if client[0] == SkipIP:
						continue

				if not self.__portMapping.get(connection['Port']):
					self.__portMapping.update({connection['Port']:{}})

				if not self.__portMapping[connection['Port']].get(client[0]):
					self.__portMapping[connection['Port']].update({client[0]:[]})

				self.__portMapping[connection['Port']][client[0]].append(client[1])

		return self.__portMapping