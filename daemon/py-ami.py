#!/usr/bin/env python
# -*- coding: utf-8 -*-

from amic import AMI
from wraps import AMIWraps
from config import config
from daemon import Daemon
from sys import argv

"""
Connection to AMI
"""


class MainAMI:
    def __init__(self):
        self.ami = AMI(config['host'], config['port'])
        self.ami.start()
        if self.ami.connect(config['login'], config['secret']):
            self.wraps = AMIWraps(self.ami)
            self.wrap_list()

    def wrap_list(self):
        self.ami.wrapper({'PeerStatus': {'function': self.wraps.peer_status,
                                         'filter': {'PeerStatus': 'Registered'}}})
        self.ami.wrapper({'PeerStatus': {'function': self.wraps.peer_status}})
        self.ami.wrapper({'ExtensionStatus': {'function': self.wraps.ext_status}})
        self.ami.wrapper({'Dial': {'function': self.wraps.dial_start,
                                   'filter': {'SubEvent': 'Begin'}}})


""" Daemonize """
class AMIDaemon(Daemon):
    def run(self):
        MainAMI()


if __name__ == '__main__':
    daemon = AMIDaemon('/tmp/ami.pid')
    if len(argv) == 2:
        if argv[1] == 'start':
            daemon.start()
        elif argv[1] == 'stop':
            daemon.stop()
        elif argv[1] == 'restart':
            daemon.restart()
        else:
            print 'Unknown argument'
    else:
        MainAMI()
