# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import base64
import SocketServer
import SimpleHTTPServer
import re
import ssl
from urlparse import urlparse
try:    import json
except Exception: import simplejson as json

import signal
import os
def signal_handler(sig, frame):
    os.kill(os.getpid(), signal.SIGTERM)
signal.signal(signal.SIGINT, signal_handler)

def printDBG(strDat):
    return
    strDat = str(strDat)
    f = open('/tmp/iptv.dbg', 'a')
    f.write(strDat + '\n')
    f.close
    print("%s" % strDat)

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def getPage(url, params={}):
    printDBG('url [%s]' % url)
    customOpeners = []
    
    try:
        if params.get('ssl_protocol', None) != None:
            ctx = ssl._create_unverified_context(params['ssl_protocol'])
        else:
            ctx = ssl._create_unverified_context()
        customOpeners.append(urllib2.HTTPSHandler(context=ctx))
    except Exception:
        pass
    
    sts = False
    data = None
    try:
        req = urllib2.Request(url)
        if 'Referer' in params:
            req.add_header('Referer', params['Referer'])
        if 'User-Agent' in params:
            req.add_header('User-Agent', params['User-Agent'])
        if 'Origin' in params:
            req.add_header('Origin', params['Origin'])
        
        printDBG("++++HEADERS START++++")
        printDBG(req.headers)
        printDBG("++++HEADERS END++++")
        
        opener = urllib2.build_opener( *customOpeners )
        resp = opener.open(req)
        data = resp.read()
        sts = True
    except Exception:
        printExc()
    return sts, data 

class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        global mainUrl
        global userAgent
        global urlPath
        global scriptUrl
        keyUrl = self.path
        
        if keyUrl.startswith('/https/'): keyUrl = 'https://' + keyUrl[7:]
        elif keyUrl.startswith('/http/'): keyUrl = 'http://' + keyUrl[6:]
        
        printDBG("do_GET: " + keyUrl)
        
        if isinstance(scriptUrl, list):
            for item in scriptUrl:
                keyUrl = keyUrl.replace(item[0], item[1])
        else:
            #keyUrl = urlPath + base64.b64encode('l=' + 'nhl' + '&g=' + 'OTT-COL-20171110' + '&f=' + 'home' + '&u=' + base64.b64encode(keyUrl))
            keyUrl = urlPath + base64.b64encode(keyUrl)
        if not keyUrl.startswith('https://') and not keyUrl.startswith('http://'): keyUrl = mainUrl + keyUrl
        parsedUri = urlparse( mainUrl )
        sts, data = getPage(keyUrl, {'User-Agent':userAgent, 'Referer':mainUrl, 'Origin':'{uri.scheme}://{uri.netloc}'.format(uri=parsedUri)})
        printDBG("sts [%s] data[%s]" % (sts, data))
        if sts:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(data)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print('Wrong parameters', file=sys.stderr)
        sys.exit(1)
    try:
        port        = int(sys.argv[1])
        hlsUrl      = sys.argv[2]
        mainUrl     = sys.argv[3]
        scriptUrl   = sys.argv[4]
        userAgent   = sys.argv[5]
        
        if scriptUrl.startswith('<proxy>'):
            urlPath = scriptUrl[7:]
            if urlPath.startswith('/'): urlPath = urlPath[1:]
        elif scriptUrl.startswith('|'):
            scriptUrl = json.loads(base64.b64decode(scriptUrl))
        else:
            urlPath = 'keys/mma.php?q='
            
            sts, data = getPage(scriptUrl, {'User-Agent':userAgent, 'Referer':mainUrl})
            if sts:
                urlPath = re.compile('''['"]([^'^"]*?keys/[^'^"]*?)['"]''').search(data)
                if urlPath == None: urlPath = re.compile('''['"]([^'^"]*?/live/[^'^"]*?)['"]''').search(data)
                if urlPath != None: urlPath = urlPath.group(1)
                if urlPath.startswith('/'): urlPath = urlPath[1:]
        
        SocketServer.TCPServer.allow_reuse_address = True
        #httpd = SocketServer.ForkingTCPServer(('127.0.0.1', port), Proxy)
        httpd = SocketServer.TCPServer(('127.0.0.1', port), Proxy)
        print('\n%s\n' % hlsUrl, file=sys.stderr)
        httpd.serve_forever()
    except KeyboardInterrupt:
        printExc()
        printDBG("Closing Server")
        httpd.shutdown()
        httpd.socket.close()
        httpd.server_close()
    sys.exit(0)

