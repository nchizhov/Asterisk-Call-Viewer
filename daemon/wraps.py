#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import email
import email.mime.text
from email.header import Header
from smtplib import SMTP
from wsc import WSocketServer
from wraps_config import config

"""
Asterisk AMI Wraps Class
"""


class AMIWraps:
    calls = {}

    def __init__(self, ami):
        self.ami = ami
        self.ws = WSocketServer(self.parse_inp, config['ws_port'])
        self.ws.start()

    def __del__(self):
        del self.ws

    def dial_start(self, data):
        if data['Uniqueid'] not in self.calls:
            self.calls.update({data['Uniqueid']: {'Caller': data['CallerIDNum'],
                                                  'To': data['DialString']}})
            self.ami.wrapper({'Hangup': {'function': self.dial_end,
                                         'filter': {'Uniqueid': data['Uniqueid']}}})
            self.ami.wrapper({'DialEnd': {'function': self.dial_status,
                                          'filter': {'Uniqueid': data["Uniqueid"]}}})

    def dial_status(self, data):
        if data['Uniqueid'] in self.calls:
            self.calls[data['Uniqueid']]['Status'] = data['DialStatus']
        self.ami.unwrapper({'DialEnd': {'filter': {'Uniqueid': data["Uniqueid"]}}})

    def dial_end(self, data):
        if data['Uniqueid'] in self.calls:
            if self.calls[data['Uniqueid']]['Status'] != 'ANSWER' and self.calls[data['Uniqueid']]['To'] in config['mail_notify']:
                self.send_mail(config['mail_notify'][self.calls[data['Uniqueid']]['To']], self.calls[data['Uniqueid']]['Caller'])
            self.calls.pop(data['Uniqueid'])
        self.ami.unwrapper({'Hangup': {'filter': {'Uniqueid': data['Uniqueid']}}})

    def peer_status(self, data):
        peer = data['Peer'].split('/')[1]
        if peer not in config['not_show']:
            sdata = {'action': 'status',
                     'peer': peer,
                     'status': data['PeerStatus']}
            self.ws.send(sdata)

    def ext_status(self, data):
        ext = data['Exten']
        if ext not in config['not_show']:
            status = ''
            if data['Status'] in ('1', '2', '8', '16'):
                status = 'busy'
            elif data['Status'] == '0':
                status = 'free'
            if status:
                sdata = {'action': 'peerstatus',
                         'peer': ext,
                         'status': status}
                self.ws.send(sdata)

    def parse_inp(self, data):
        action = data['action']
        if action == 'start':
            sdata = {'action': 'peers',
                     'peers': list()}
            peers = self.ami.getpeers('sip') + self.ami.getpeers('iax') + self.ami.getpeers('pjsip')
            peernames = self.ami.getpeerext()
            for peer in peers:
                ext = peer['ObjectName']
                if ext not in config['not_show']:
                    status = 'offline'
                    if 'Status' in peer:
                        if peer['Status'].split(' ')[0] == 'OK':
                            tmpstatus = self.ami.getpeerstatus(ext)
                            if tmpstatus in ('1', '2', '8', '16'):
                                status = 'busy'
                            elif tmpstatus == '0':
                                status = 'free'
                    elif 'DeviceState' in peer:
                        deviceState = "".join(peer['DeviceState'].lower().split())
                        if deviceState == 'notinuse':
                            status = 'free'
                        elif deviceState in ('inuse', 'busy', 'ringing', 'ringinginuse', 'onhold'):
                            status = 'busy'
                    sdata['peers'].append({'number': ext,
                                           'name': peernames[ext] if ext in peernames else '',
                                           'status': status})
            self.ws.send(sdata, data['id'])

    def send_mail(self, to, number):
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        message = """
        У вас есть пропущенный звонок с номера <b>%s</b><br /><br /><br />
        <hr /><br />
        <i>Робот</i>
        """ % number
        smtp = SMTP()
        smtp.set_debuglevel(debuglevel=0)
        smtp.connect(config['mail']['address'], config['mail']['port'])
        smtp.starttls()
        smtp.login(config['mail']['login'], config['mail']['password'])
        emailmsg = email.MIMEMultipart.MIMEMultipart('alternative')
        emailmsg.set_charset('utf8')
        emailmsg['Subject'] = Header('Пропущенный звонок', 'UTF-8')
        emailmsg['From'] = config['mail']['from']
        emailmsg['To'] = to
        emailmsg['Date'] = date
        emailmsg.attach(email.mime.text.MIMEText(message, 'html', 'UTF-8'))
        smtp.sendmail(config['mail']['from'], to, emailmsg.as_string())
        smtp.close()
