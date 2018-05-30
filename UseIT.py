from GNSTopology import *

mappeds = []

for host in ['10.0.0.1']:
	mappeds.append(Mapper(host=host,username='danszabo'))


GNS = GenerateGNS(name='home',Mappings=mappeds)
GNS.processNodes()
GNS.saveTopology()