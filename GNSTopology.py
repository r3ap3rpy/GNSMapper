import json

from Mapper import *
from uuid import uuid4
from math import sin,cos,pi

class GenerateGNS(object):
	__toProcess = []
	__jSkeleton = None
	__nodeUuids = {}
	__linkInfo = []
	__portCounter = {}
	__additionalNodes = []
	__skeleton = """
{
    "auto_close": true,
    "auto_open": false,
    "auto_start": false,
    "grid_size": 75,
    "name": "",
    "project_id": "",
    "revision": 8,
    "scene_height": 1000,
    "scene_width": 2000,
    "show_grid": false,
    "show_interface_labels": true,
    "show_layers": false,
    "snap_to_grid": false,
    "topology": "",
    "type": "topology",
    "version": "2.1.5",
    "zoom": 100
}
	"""
	def __init__(self, name, Mappings):
		self.projectName = name
		self.__jSkeleton = dict(json.loads(self.__skeleton))
		self.__jSkeleton['name'] = self.projectName
		self.__jSkeleton['project_id'] = str(uuid4())
		self.__jSkeleton['topology'] = {"nodes":[],"links":[],"drawings":[],"computes": []}
		if isinstance(Mappings,list):
			for m in Mappings:
				if not isinstance(m,Mapper):
					raise Exception('The object needs to be an instance of the mapping class!')
				else:
					if m.clientInfo is None:
						m.get_clients()
					self.__toProcess.append(m)

		elif isinstance(Mappings,Mapper):
			print("Processing: {}".format(Mappings))
			print('Checkcing: {} ({})'.format(Mappings.realname, Mappings.ipaddr))
			if not isinstance(Mappings, Mapper):
				raise Exception('The object needs to be an instance of the mapping class!')
			else:
				if Mappings.clientInfo is None:
					Mappings.get_clients()
				self.__toProcess.append(Mappings)
		else:
			raise Exception("Mappings have to be an array of the Mapping objects!")

	def processNodes(self, Logging = False):
		self.__jSkeleton["scene_width"] = 500 * len(self.__toProcess) 

		for node in self.__toProcess:
			if not self.__nodeUuids.get(node.ipaddr):
				self.__nodeUuids.update({node.ipaddr:str(uuid4())})

			for port in node.clientInfo:
				for ip in node.clientInfo[port]:
					if not self.__nodeUuids.get(ip):
						self.__nodeUuids.update({ip:str(uuid4())})
		if Logging:
			with open('Logs.txt','w') as f:
				pprint('############## Initial data #############',stream=f)
				for node in self.__toProcess:
					pprint(node.clientInfo,stream=f)

			with open('Logs.txt','a') as f:
				pprint('############## node uuids #############',stream=f)
				pprint(self.__nodeUuids,stream=f)

		index = 0
		cX = -int((500 * len(self.__toProcess)) / 2 - 250)
		cY = -200

		# Pulling master node data!
		for node in self.__toProcess:
			nodeinfo = {}
			nodeinfo["compute_id"]= "local"
			nodeinfo["console"]= 5004
			nodeinfo["console_type"]= "telnet"
			nodeinfo["first_port_name"]= "null"
			nodeinfo["height"]= 70
			nodeinfo["label"] = {
				"rotation": 0,
				"style": "font-family: TypeWriter;font-size: 10.0;font-weight: bold;fill: #000000;fill-opacity: 1.0;",
				"text": "Ethernetswitch-1",
				"x": -13,
				"y": -25
				}
			nodeinfo["name"] = node.realname
			nodeinfo["node_id"] = self.__nodeUuids[node.ipaddr]
			nodeinfo["node_type"] = "ethernet_switch"
			nodeinfo["port_name_format"] = "{0}"
			nodeinfo["port_segment_size"] = 0
			nodeinfo["properties"] = {"ports_mapping":[]}
			nodeinfo["symbol"] =  ":/symbols/server.svg"
			nodeinfo["width"] = 49
			nodeinfo["z"] = 0

			nodeinfo["x"] = cX
			nodeinfo["y"] = cY
			if index % 2 == 0:
				cY += 350
			else:
				cY -= 350
			cX += 400

			index += 1

			pindex = 0
			for port in node.clientInfo:
				for ip in node.clientInfo[port]:
					portinfo = {}
					portinfo["name"] = port
					portinfo["port_number"] = pindex
					portinfo["type"] = "access"
					portinfo["vlan"] = 1
					nodeinfo["properties"]["ports_mapping"].append(portinfo)
					pindex += 1

			self.__jSkeleton["topology"]["nodes"].append(nodeinfo)

		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## skeleton after first round of nodes #############',stream=f)
				pprint(self.__jSkeleton,stream=f)

		# Pulling link information
		for node in self.__toProcess:
			for jnode in self.__toProcess:
				if node.ipaddr != jnode.ipaddr:
					for port in jnode.clientInfo:
						if node.ipaddr in jnode.clientInfo[port].keys():
							if not self.__portCounter.get(jnode.ipaddr):
								try: 
									self.__portCounter[jnode.ipaddr] += 1
								except:
									self.__portCounter.update({jnode.ipaddr:0})
							else:
								self.__portCounter[jnode.ipaddr] += 1

							if not self.__portCounter.get(node.ipaddr):
								try: 
									self.__portCounter[node.ipaddr] += 1
								except:
									self.__portCounter.update({node.ipaddr:0})
							else:
								self.__portCounter[node.ipaddr] += 1
							self.__linkInfo.append([jnode.ipaddr,node.ipaddr,port,self.__portCounter[jnode.ipaddr],self.__portCounter[node.ipaddr]])
		
		# Pulling link information
		for node in self.__toProcess:
			for port in node.clientInfo:
				for ip in node.clientInfo[port].keys():
					if not [ip,node.ipaddr,port] in self.__linkInfo:
						self.__additionalNodes.append(ip)
						if not self.__portCounter.get(ip):
							try: 
								self.__portCounter[ip] += 1
							except:
								self.__portCounter.update({ip:0})
						else:
							self.__portCounter[ip] += 1

						if not self.__portCounter.get(node.ipaddr):
							try: 
								self.__portCounter[node.ipaddr] += 1
							except:
								self.__portCounter.update({node.ipaddr:0})
						else:
							self.__portCounter[node.ipaddr] += 1
						self.__linkInfo.append([ip,node.ipaddr,port,self.__portCounter[ip],self.__portCounter[node.ipaddr]])
		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## linkinfo #############',stream=f)
				pprint(self.__linkInfo,stream=f)

		# Pulling additional leaf node information!
		for node in self.__additionalNodes:
			#for processed in self.__jSkeleton["topology"]["nodes"]:
			alreadyProcessed = [_["node_id"] for _ in self.__jSkeleton["topology"]["nodes"] ]
			if not self.__nodeUuids[node] in alreadyProcessed:
				#if not processed["node_id"] == self.__nodeUuids[node]:
				nodeinfo = {}
				nodeinfo["compute_id"]= "local"
				nodeinfo["console"]= 5004
				nodeinfo["console_type"]= "telnet"
				nodeinfo["first_port_name"]= "null"
				nodeinfo["height"]= 70
				nodeinfo["label"] = {
					"rotation": 0,
					"style": "font-family: TypeWriter;font-size: 10.0;font-weight: bold;fill: #000000;fill-opacity: 1.0;",
					"text": "Ethernetswitch-1",
					"x": -13,
					"y": -25
					}
				try:
					rname = socket.gethostbyaddr(node)[0]
				except:
					rname = node
				nodeinfo["name"] = rname
				nodeinfo["node_id"] = self.__nodeUuids[node]
				nodeinfo["node_type"] = "ethernet_switch"
				nodeinfo["port_name_format"] = "{0}"
				nodeinfo["port_segment_size"] = 0
				nodeinfo["properties"] = {}
				nodeinfo["symbol"] =  ":/symbols/server.svg"
				nodeinfo["width"] = 49
				nodeinfo["x"] = -191
				nodeinfo["y"] = 48
				nodeinfo["z"] = 0
				self.__jSkeleton["topology"]["nodes"].append(nodeinfo)
				#break
		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## skeleton after additional nodes #############',stream=f)
				pprint(self.__jSkeleton,stream=f)

		# Adding links to the nodes!
		for item in self.__linkInfo:
			if len(item) != 5:
				continue
			linkinfo = {}
			
			linkinfo["nodes"] = []
			linkinfo["filters"] = {}
			linkinfo["link_id"] = str(uuid4())
			linkinfo["suspend"] = False

			linknode = {}
			linknode["adapter_number"] = 0
			linknode["label"] = { 
					"rotation" : 0,
					"style" : "font-family: TypeWriter;font-size: 10.0;font-weight: bold;fill: #000000;fill-opacity: 1.0;",
					"text":item[2],
					"x": 58,
					"y": 13
				}
			linknode["node_id"] = self.__nodeUuids[item[0]]
			linknode["port_number"] = item[3]
			linkinfo["nodes"].append(linknode)

			linknode = {}
			linknode["adapter_number"] = 0
			linknode["label"] = { 
					"rotation" : 0,
					"style" : "font-family: TypeWriter;font-size: 10.0;font-weight: bold;fill: #000000;fill-opacity: 1.0;",
					"text":"",
					"x": 58,
					"y": 13
				}

			linknode["node_id"] = self.__nodeUuids[item[1]]
			linknode["port_number"] = item[4]
			linkinfo["nodes"].append(linknode)

			self.__jSkeleton["topology"]["links"].append(linkinfo)

		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## skeleton after linkinfo #############',stream=f)
				pprint(self.__jSkeleton,stream=f)

		## Adjusting node numbers based on extra connections that go from and to the specified node!
		for node in self.__toProcess:
			for info in self.__jSkeleton["topology"]["nodes"]:
				if info["name"] == node.realname and info["properties"].get("ports_mapping"):
					ctr = 0
					for link in self.__linkInfo:
						if link[0] == node.ipaddr or link[1] == node.ipaddr:
							ctr += 1

					if ctr > len(info["properties"]["ports_mapping"]):
						for i in range(len(info["properties"]["ports_mapping"]),ctr):
							info["properties"]["ports_mapping"].append({'name': '8215', 'port_number': i,'type': 'access','vlan': 1})

		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## skeleton after extending the ports #############',stream=f)
				pprint(self.__jSkeleton,stream=f)

		## Adjusting coordinates of the related leaf nodes!
		NodeIPs = [ _.ipaddr for _ in self.__toProcess ]
		AlreadyAdjusted = []
		for ip in NodeIPs:
			relatedNodes = []
			for link in self.__linkInfo:
				if ip in link:
					relatedNodes.append(link)
			
			radius = 225			
			index = 1
			decrement = 0
			for link in relatedNodes:
				sliceof = 2 * pi / (len(relatedNodes) - decrement)
				link.remove(ip)
				if len(link) == 3:
					continue
				if link[0] in NodeIPs:
					continue

				if link[0] in AlreadyAdjusted:
					decrement += 1
					continue
				else:
					AlreadyAdjusted.append(link[0])
				NodeToModify = [ _ for _ in self.__jSkeleton["topology"]["nodes"] if _["node_id"] == self.__nodeUuids[link[0]] ]
				MasterNode = [_ for _ in self.__jSkeleton["topology"]["nodes"] if _["node_id"] == self.__nodeUuids[ip] ]

				NodeToModify[0]['x'] = int(MasterNode[0]['x'] + radius * cos(sliceof * index))
				NodeToModify[0]['y'] = int(MasterNode[0]['y'] + radius * sin(sliceof * index))
				index += 1
		if Logging:
			with open('Logs.txt','a') as f:
				pprint('############## final look #############',stream=f)
				pprint(self.__jSkeleton,stream=f)

		return self.__jSkeleton

	def showJson(self):
		''' Returns the skeleton of the gns3 definition file! '''
		return self.__jSkeleton

	def saveMiserables(self):
		if self.__jSkeleton is None:
			raise Exception("The process nodes need to be called first!")
		else:
			Miserables = {"nodes":[],"links":[]}

			for node in self.__jSkeleton["topology"]["nodes"]:
				if node["properties"].get("ports_mapping"):
					Miserables["nodes"].append({"id":node["node_id"],"group":len(node["properties"]["ports_mapping"])})
				else:
					Miserables["nodes"].append({"id":node["node_id"],"group":0})

			for link in self.__jSkeleton["topology"]["links"]:
				Miserables["links"].append({"source":link["nodes"][0]["node_id"],"target":link["nodes"][1]["node_id"],"value":1})


			with open("miserables.json",'w') as f:
				f.write(json.dumps(Miserables))


	def saveTopology(self):
		''' Saves the json file which represents the GNS topology to a specific file!'''
		with open(self.projectName + '.gns3','w') as f:
			f.write(json.dumps(self.__jSkeleton))
