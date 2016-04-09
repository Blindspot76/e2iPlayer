# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import time

def printDBG(strDat):
    if 0:
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
    sts = False
    data = None
    try:
        req = urllib2.Request(url)
        if 'Referer' in params:
            req.add_header('Referer', params['Referer'])
        if 'User-Agent' in params:
            req.add_header('User-Agent', params['User-Agent'])
        resp = urllib2.urlopen(req)
        data = resp.read()
        sts = True
    except:
        printExc()
    return sts, data

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print('User-Agent, Referer and two refresh urls are needed', file=sys.stderr)
        sys.exit(1)
    try:
        timeout = 20 # 20s
        userAgent   = sys.argv[1]
        referer     = sys.argv[2]
        refreshUrl1 = sys.argv[3]
        refreshUrl2 = sys.argv[4]
        
        while True:
            printDBG("Refreshing....")
            start_time = time.time()
            for url in [refreshUrl1, refreshUrl2]:
                sts, data = getPage(url, {'Referer':referer, 'User-Agent':userAgent})
                printDBG("[%s][%s]" % (sts, data))
            dt = time.time() - start_time
            if dt > 0 and dt < 20:
                time.sleep(20 - dt)
    except:
        printExc()
    sys.exit(0)

