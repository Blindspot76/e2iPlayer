# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import time
import json

def printDBG(strDat):
    if 1:
        print("%s" % strDat)

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def getPage(url, params={}, post_data=None):
    printDBG('url [%s]' % url)
    sts = False
    data = None
    try:
        req = urllib2.Request(url, post_data, params)
        if 0:
            if 'Referer' in params:
                req.add_header('Referer', params['Referer'])
            if 'User-Agent' in params:
                req.add_header('User-Agent', params['User-Agent'])
            if 'Cookie' in params:
                req.add_header('Cookie', params['Cookie'])
        resp = urllib2.urlopen(req)
        data = resp.read()
        sts = True
    except:
        printExc()
    return sts, data
    
def getTimestamp(t, s=64):
    a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    e = ""
    t = int(t)
    while t > 0:
        e = a[t % s] + e
        t = int(t / s)
    return e

if __name__ == "__main__":
    if len(sys.argv) < 9:
        print('User-Agent, BaseUrl, two refresh urls, stoken, streamId and libsPath are needed', file=sys.stderr)
        sys.exit(1)
    try:
        timeout = 20 # 20s
        userAgent   = sys.argv[1]
        baseUrl     = sys.argv[2]
        refreshUrl1 = sys.argv[3]
        refreshUrl2 = sys.argv[4]
        stoken      = sys.argv[5]
        streamId    = sys.argv[6]
        libsPath    = sys.argv[7]
        sid         = sys.argv[8]
        
        sys.path.insert(1, libsPath)
        import websocket
        
        ws1 = websocket.create_connection(refreshUrl1)
        ws2 = websocket.create_connection(refreshUrl2)
        
        ws1.send('2probe')
        ws2.send('2probe')
        
        result = ws1.recv()
        result = ws2.recv()
        
        ws1.send('5')
        ws2.send('5')
        
        if 0:
            t2 = getTimestamp(time.time()*1000)
            url = baseUrl.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, sid)
            sts, data = getPage(url, {'User-Agent':userAgent, 'Cookie':sid}, '84:42["subscribe","%s"]' % streamId)
            print(data)

        ws1.send('42["subscribe","%s"]' % streamId)
        result = ws1.recv()
        print(result)
        result = json.loads(result[result.find('42')+2:])
        vidUrl = baseUrl + '/' + result[1]['url'] + '?token=' + stoken
        print('\n%s\n' % vidUrl, file=sys.stderr)
        
        if 0:
            ws1.send('2')
            ws2.send('2')
            result = ws1.recv()
            result = ws2.recv()
        
        start_time = time.time()
        result = ['', '']
        while True:
            printDBG("Refreshing....")
            
            if 0:
                #ws1.send('2')
                #result[0] = ws1.recv()
                print(result[0])
                ws1.send('42["subscribe","%s"]' % streamId)
                result[0] = ws1.recv()
                print(result[0])
                result[0] = json.loads(result[0][result[0].find('42')+2:])
                vidUrl = baseUrl + '/' + result[0][1]['url'] + '?token=' + stoken
                print('\n%s\n' % vidUrl, file=sys.stderr)
            
            dt = time.time() - start_time
            if dt >= 0 and dt < 20:
                time.sleep(20 - dt)
            
            ws1.send('2')
            ws2.send('2')
            result[0] = ws1.recv()
            result[1] = ws2.recv()
            print(result, file=sys.stderr)
            
            if 0:
                #42["stream_restart",{"event":"stream_restart","server":"http://109.236.84.53:8000","streamId":"219532349db1cc6aa31971dc4d593e68896bdd2a90fff4d659812c54f1f6928094"}]
                for item in result:
                    if 'stream_restart' in item:
                        item = json.loads(item[item.find('42')+2:])
                        vidUrl = baseUrl + '/' + item[1]['url'] + '?token=' + stoken
                        print('\n%s\n' % vidUrl, file=sys.stderr)
            
            start_time = time.time()
                    

        ws1.close()
        ws2.close()
    except:
        printExc()
    sys.exit(0)

