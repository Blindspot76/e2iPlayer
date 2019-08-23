# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc,GetCookieDir 
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unicode_escape

class openload(CBaseHostClass):
    
        def __init__(self):
                CBaseHostClass.__init__(self,{'cookie':'google.cookie'})
                
      
        def parserOPENLOAD(self, baseUrl):
            printDBG("parserOPENLOAD baseUrl[%s]" % baseUrl)
            
            videoTab = []

            header = {}
            if "|" in baseUrl:
                page_url, referer = page_url.split("|", 1)
                header = {'Referer': referer}
                HTTP_HEADER
            else:
                HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
                HTTP_HEADER['Referer'] = baseUrl
                
            COOKIE_FILE = GetCookieDir('openload.cookie')
            print 'COOKIE_FILE',COOKIE_FILE
            defaultParams = {'header': HTTP_HEADER, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
            
            sts, data = self.cm.getPage(baseUrl, defaultParams)
            if not sts: return []
            

            
            subtitle = self.cm.ph.getSearchGroups(data, '<track kind="captions" src="([^"]+)" srclang="es"')[0]

            try:
                code = self.cm.ph.getSearchGroups(data, '<p style="" id="[^"]+">(.*?)</p>' )[0]
                _0x59ce16 = eval(self.cm.ph.getSearchGroups(data, '_0x59ce16=([^;]+)')[0].replace('parseInt', 'int'))
                _1x4bfb36 = eval(self.cm.ph.getSearchGroups(data, '_1x4bfb36=([^;]+)')[0].replace('parseInt', 'int'))
                parseInt  = eval(self.cm.ph.getSearchGroups(data, '_0x30725e,(\(parseInt.*?)\),')[0].replace('parseInt', 'int'))
                url = self.decode(code, parseInt, _0x59ce16, _1x4bfb36)
                #print "url",url
                #url2 = self.cm.getPage(url).headers.get('location')
                #print "url2",url2
                #videoTab.append(('mp4',url))
                videoTab.append({'url': url, 'name': 'openload.co (mp4)'})
                return videoTab
                sts, data = self.cm.getPage(url, defaultParams)
                print "data",data
                if not sts: return []
                


                

                extension = self.cm.ph.getSearchGroups(url, '(\..{,3})\?')[0]
                print "extension",extension
                #videoTab.append([extension, url, 0,subtitle])
                videoTab.append({'url': url, 'name': 'openload.co ('+extension+')'})	
                print "videoTab",videoTab
            except Exception:
                printExc()
                
            return videoTab


        def decode(self,code, parseInt, _0x59ce16, _1x4bfb36):
          
            import math

            _0x1bf6e5 = ''
            ke = []

            for i in range(0, len(code[0:9*8]),8):
                ke.append(int(code[i:i+8],16))

            _0x439a49 = 0
            _0x145894 = 0

            while _0x439a49 < len(code[9*8:]):
                _0x5eb93a = 64
                _0x896767 = 0
                _0x1a873b = 0
                _0x3c9d8e = 0
                while True:
                    if _0x439a49 + 1 >= len(code[9*8:]):
                        _0x5eb93a = 143;

                    _0x3c9d8e = int(code[9*8+_0x439a49:9*8+_0x439a49+2], 16)
                    _0x439a49 +=2

                    if _0x1a873b < 6*5:
                        _0x332549 = _0x3c9d8e & 63
                        _0x896767 += _0x332549 << _0x1a873b
                    else:
                        _0x332549 = _0x3c9d8e & 63
                        _0x896767 += int(_0x332549 * math.pow(2, _0x1a873b))

                    _0x1a873b += 6
                    if not _0x3c9d8e >= _0x5eb93a: break

                # _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ _0x59ce16 ^ parseInt ^ _1x4bfb36
                _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ parseInt ^ _1x4bfb36
                _0x2de433 = _0x5eb93a * 2 + 127

                for i in range(4):
                    _0x3fa834 = chr(((_0x30725e & _0x2de433) >> (9*8/ 9)* i) - 1)
                    if _0x3fa834 != '$':
                        _0x1bf6e5 += _0x3fa834
                    _0x2de433 = (_0x2de433 << (9*8/ 9))

                _0x145894 += 1


            url = "https://openload.co/stream/%s?mime=true" % _0x1bf6e5
            return url
                         

def get_video_url(url):
    host=openload()
    return host.parserOPENLOAD(url)
    

