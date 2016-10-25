"""Custom loop topo example

   There are two paths between host1 and host2.
                          host2
                            |
                         switch2
                            |
   host1 --- switch1-----switch5-------switch4 -----host4
                            |
                         switch3
                            |
                          host3

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import logging
import os

logging.basicConfig(filename='./fattree.log', level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTopo(Topo):
    "Simple loop topology example."

    HostList = []
    SwitchList = []

    def __init__(self):
        # Init Topo
        Topo.__init__(self)

    def createHost(self):
        for i in range(1, 13):
            self.HostList.append(self.addHost('h' + str(i)))
            self.SwitchList.append(self.addSwitch('s' + str(i)))

    def createLink(self, bw_mb, delay_ms):
        # Add links
        for i in range(12):
            self.addLink(self.SwitchList[i], self.HostList[i], bw=bw_mb, delay=delay_ms)

            #       edge_list = [(1, 2), (1, 12), (2, 1), (2, 3), (2, 12), (3, 2), (3, 4), (3, 10), (4, 3), (4, 5), (4, 8),
            #                    (5, 4), (5, 6), (6, 5), (6, 7), (7, 6), (7, 8), (8, 4), (8, 7), (8, 9), (8, 10), (9, 8),
            #                    (10, 3), (10, 8), (10, 11), (11, 10), (11, 12), (12, 1), (12, 2), (12, 11)]

        edge_list = [(1, 2), (2, 1), (2, 3), (2, 12), (3, 2), (3, 4), (4, 3), (4, 5), (4, 8),
                     (5, 4), (6, 7), (7, 6), (7, 8), (8, 4), (8, 7), (8, 9), (8, 10), (9, 8),
                     (10, 8), (10, 11), (11, 10), (11, 12), (12, 2), (12, 11)]

        for edge in edge_list:
            self.addLink(self.SwitchList[edge[0] - 1], self.SwitchList[edge[1] - 1], bw=bw_mb, delay=delay_ms)

    def set_ovs_protocol_13(self):
        for sw in self.SwitchList:
            cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
            os.system(cmd)


def iperfTest(net, topo):
    logger.debug("Start iperfTEST")
    h0, h1, h2 = net.get(
            topo.HostList[0], topo.HostList[1], topo.HostList[2])

    # iperf Server
    h0.popen(
            'iperf -s -u -i 1 > iperf_server_differentPod_result', shell=True)

    # iperf Server
    h1.popen(
            'iperf -s -u -i 1 > iperf_server_samePod_result', shell=True)

    # iperf Client
    h2.cmdPrint('iperf -c ' + h0.IP() + ' -u -t 10 -i 1 -b 20m')
    h2.cmdPrint('iperf -c ' + h1.IP() + ' -u -t 10 -i 1 -b 20m')


def pingTest(net):
    logger.debug("Start Test all network")
    net.pingAll()


def createTopo():
    "Create network and run simple performance test"
    controller_ip = "127.0.0.1"
    controller_port = 6633

    topo = SimpleTopo()
    topo.createHost()
    topo.createLink(25, '25ms')

    net = Mininet(topo=topo, link=TCLink, controller=None)
    net.addController(
            'controller', controller=RemoteController,
            ip=controller_ip, port=controller_port)
    net.start()

    '''
        Set OVS's protocol as OF13
    '''
    topo.set_ovs_protocol_13()

    logger.debug("dumpNode")

    dumpNodeConnections(net.hosts)
    #  pingTest(net)
    #  iperfTest(net, topo)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createTopo()
