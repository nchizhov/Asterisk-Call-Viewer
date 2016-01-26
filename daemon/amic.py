#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import time
import random


class AMI(threading.Thread):
    eols = 1
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.waitConnect = False
        self.action = {}
        self.wraps = []
        threading.Thread.__init__(self)

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        sdata = ''
        try:
            while True:
                data = self.sock.recv(10240)
                if not data:
                    break
                else:
                    if data.split('\r\n' * self.eols)[-1]:
                        sdata += data
                    else:
                        self.__parseAMI(sdata + data)
                        sdata = ''
        finally:
            self.sock.close()

    def stop(self):
        sdata = {'Action': 'logoff'}
        self.__sendCommand(sdata)

    """ parsing AMI """
    def __parseAMI(self, data):
        #print repr(data)
        if 'Asterisk Call Manager' in data:
            self.eols = 2
            self.waitConnect = True
        else:
            data = data.split('\r\n')
            tmp_data = {}
            for line in data:
                if line.strip():
                    try:
                        command, response = line.split(': ')
                        tmp_data[command] = response.strip()
                    except:
                        tmp_data['raw_data'] = line
                else:
                    if 'ActionID' in tmp_data:
                        actionid = tmp_data['ActionID']
                        if actionid in self.action:
                            if self.action[actionid]['action'] == 'login':
                                self.action[actionid]['data'] = tmp_data
                                self.action[actionid]['wait'] = False
                            elif self.action[actionid]['action'] in ('Sippeers', 'Iaxpeerlist'):
                                if 'Event' in tmp_data:
                                    if tmp_data['Event'] == 'PeerEntry':
                                        self.action[actionid].setdefault('data', list()).append(tmp_data)
                                    elif tmp_data['Event'] == 'PeerlistComplete':
                                        self.action[actionid]['wait'] = False
                            elif self.action[actionid]['action'] == 'peerext':
                                self.action[actionid]['data'] = tmp_data
                                self.action[actionid]['wait'] = False
                            elif self.action[actionid]['action'] == 'peerstatus':
                                self.action[actionid]['data'] = tmp_data
                                self.action[actionid]['wait'] = False
                            else:
                                pass
                    elif 'Event' in tmp_data:
                        # print tmp_data
                        event = tmp_data['Event']
                        for wrap in self.wraps:
                            if event in wrap:
                                if 'filter' in wrap[event]:
                                    cfilters = len(wrap[event]['filter'])
                                    for sevent, sresponse in wrap[event]['filter'].items():
                                        if sevent in tmp_data and tmp_data[sevent] == sresponse:
                                            cfilters -= 1
                                    if not cfilters:
                                        wrap[event]['function'](tmp_data)
                                else:
                                    wrap[event]['function'](tmp_data)
                            else:
                                pass
                                # print tmp_data
                    tmp_data = {}

    """ Connecting """
    def connect(self, login, secret):
        actionid = self.__genActionID('login')
        sdata = {'Action': 'login',
                 'ActionID': actionid,
                 'Username': login,
                 'Secret': secret}
        while True:
            if self.waitConnect:
                self.__sendCommand(sdata)
                break
        while self.action[actionid]['wait']:
            pass
        data = self.action[actionid]['data']
        del self.action[actionid]
        if data['Message'] == 'Authentication accepted':
            return True
        else:
            return False

    """ Get sip/aix2 peers """
    def getpeers(self, peertype = 'sip'):
        peer = 'Iaxpeerlist' if peertype.lower() == 'iax' else 'Sippeers'
        actionid = self.__genActionID(peer)
        sdata = {'Action': peer,
                 'ActionID': actionid}
        self.__sendCommand(sdata)
        while self.action[actionid]['wait']:
            pass
        data = self.action[actionid]['data'] if 'data' in self.action[actionid] else []
        del self.action[actionid]
        return data

    def getpeerext(self):
        actionid = self.__genActionID('peerext')
        sdata = {'Action': 'Command',
                 'ActionID': actionid,
                 'Command': 'database showkey cidname'}
        self.__sendCommand(sdata)
        while self.action[actionid]['wait']:
            pass
        exts = {}
        data = self.action[actionid]['data']
        del self.action[actionid]
        lines = data['raw_data'].split('\n')
        for line in lines:
            try:
                ext, name = line.split(':')
                exts[ext.split('/')[2]] = name.strip()
            except:
                pass
        return exts

    def getpeerstatus(self, ext):
        actionid = self.__genActionID('peerstatus')
        sdata = {'Action': 'ExtensionState',
                 'ActionID': actionid,
                 'Context': 'from-internal',
                 'Exten': ext}
        self.__sendCommand(sdata)
        while self.action[actionid]['wait']:
            pass
        data = self.action[actionid]['data']
        del self.action[actionid]
        return data['Status']

    """Setting wrapper"""
    def wrapper(self, event):
        if isinstance(event, dict):
            self.wraps.append(event)

    """
    Unsetting wrapper
    event format: {'event': {'filter': {'filter1': 'data'}}} OR
    'event' as string
    """
    def unwrapper(self, event):
        if isinstance(event, dict) and len(event) == 1:
            event_name = event.keys()[0]
            if 'filter' in event[event_name] and isinstance(event[event_name], dict):
                for idx, wrap in enumerate(self.wraps):
                    if event_name in wrap and 'filter' in wrap[event_name] and wrap[event_name]['filter'] == event[event_name]['filter']:
                        self.wraps.pop(idx)
        elif isinstance(event, str):
            for idx, wrap in enumerate(self.wraps):
                if event in wrap:
                    self.wraps.pop(idx)

    """commands for AMI"""
    def command(self, data):
        if isinstance(data, dict) and 'Action' in data:
            data["ActionID"] = self.__genActionID(data['Action'])
            self.__sendCommand(data)

    """ sending Commands """
    def __sendCommand(self, data):
        comm_line = ''
        for comm, val in data.iteritems():
            comm_line += "%s: %s\r\n" % (comm, val)
        if comm_line:
            # print comm_line
            self.sock.sendall('%s\r\n' % comm_line)

    """ Generate ActionID """
    def __genActionID(self, action):
        id = '%s%s' % (time.time(), random.randint(1, 100000))
        self.action[id] = {'action': action,
                           'wait': True}
        return id