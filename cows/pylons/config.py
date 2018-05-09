# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Miscellaneous utility functions/classes

#load csml config options
#starts symlink checker
#send email (used by symlink checker


"""

import os, time
import pylons
from threading import Thread
import logging
log=logging.getLogger(__name__)

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
import smtplib
from cows.service.imps.csmlbackend.config import config


def configCSML(app_config=None):
    """Initialise the configuration of the CSML backend from pylons.config.

    For Pylons>=1.0 the pylons.config object is passed in explicitly.
    If app_config=None Pylons-0.9.6.1 behaviour is assumed.

    """
    
    if app_config is None:
        app_config = pylons.config

    for k in app_config:
        parts = k.split('.')
        if parts[:2] == ['cows', 'csml']:
            k2 = '.'.join(parts[2:])
            config[k2] = app_config[k]
    
    #set up the CSML symlink checker to check all symlinks in the csmlstore
    #Symlink checker is currently set to check hourly but can be modified in the pylons ini file by changing csml.cows.symlink_check_interval (in minutes).  
    if config.has_key('symlink_check_interval'):
        minutes=float(config['symlink_check_interval'])
    else:
        #default to hourly checks
        minutes=60
    paths = getCSMLPaths(config['csmlstore'])
    startSymLinkChecker(paths, minutes)
        
def getCSMLPaths(csmldirectory):   
    paths=[]
    for dirpath, dirnames, filenames in os.walk(csmldirectory):
        for filename in filenames:
            file_id, ext = os.path.splitext(filename)
            if ext in ('.xml', '.csml'):
                paths.append(os.path.join(dirpath, filename))
    return paths

def startSymLinkChecker(paths, minutes):
    checkerProcess = SymlinkChecker(paths, minutes)
    checkerProcess.start()

class SymlinkChecker(Thread):
    ''' This creates a new thread which sleeps most of the time, but occasionally checks that the CSML symlinks are working.'''
    def __init__ (self,paths, sleepminutes):
        Thread.__init__(self)
        #self.setDaemon(True)
        self.paths=paths
        self.sleepminutes=sleepminutes 
    
    def run(self):
        while 1:
            for path in self.paths:
                if os.path.islink(path):
                    #it's a symlink, get the link path 
                    symlinkpath=os.readlink(path)
                    #this may be relative so make sure it isn't
                    fullsymlinkpath=os.path.join(os.path.abspath(os.path.dirname(path) ), symlinkpath)
                    #now check it's not broken.
                    if not os.path.exists(fullsymlinkpath):
                        #if broken, send notification email (if configured) and log a warning message
                        if config.has_key('send_symlink_warnings_to'):
                            if config.has_key('send_symlink_warnings_from'):
                                if config.has_key('symlink_warnings_smtp'):
                                    to=config['send_symlink_warnings_to'].split(',')
                                    fro=config['send_symlink_warnings_from']
                                    smtp=config['symlink_warnings_smtp']
                                    subject = 'Broken Symlink in visualisation software'
                                    message= 'This message is from the COWS pylons application. Symlink %s is broken' % path
                                    sendemail(fro, to, subject, message, smtp)
                        log.warning('INVESTIGATE: Symlink %s is broken ' % path)
                    else:
                        log.info('Symlink OK: %s '%path)
            time.sleep(self.sleepminutes*60)
    
def sendemail(fro, to, subject, message, smtp):
    ''' send an email '''
    SERVER = smtp
    FROM = fro
    TO = to # must be a list
    SUBJECT = subject
    TEXT = message
    
    #create the message
    msg = MIMEMultipart()
    msg['From'] = FROM
    msg['To'] = COMMASPACE.join(TO)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = SUBJECT
    msg.attach( MIMEText(TEXT) )

    # Send the mail
    server = smtplib.SMTP(SERVER)
    server.sendmail(FROM, TO, msg.as_string())
    server.quit()
        
        
               


    
