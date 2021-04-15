# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit    import TranslateTXT as _, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes              import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.asynccall         import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.pCommon       import common, CParsingHelper
#from Plugins.Extensions.IPTVPlayer.libs.pCommon                import common, CParsingHelper 
from Plugins.Extensions.IPTVPlayer.libs.urlparser               import urlparser
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser     import urlparser as ts_urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools              import CSearchHistoryHelper, GetCookieDir, printDBG, printExc
from Plugins.Extensions.IPTVPlayer.libs.e2ijson                 import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc   import AES_CBC

from Components.config import config
import os
import re
import base64
import hashlib
import urllib,cookielib,time
import threading
import sys

black,white,gray='\c00000000','\c00??????','\c00808080'
blue,green,red,yellow,cyan,magenta='\c000000??','\c0000??00','\c00??0000','\c00????00','\c0000????','\c00??00??'

tunisia_gouv = [("", "None"),("Tunis","Tunis"),("Ariana","Ariana"),("Béja","Béja"),("Ben Arous","Ben Arous"),("Bizerte","Bizerte"),\
                ("Gab%E8s","Gabès"),("Gafsa","Gafsa"),("Jendouba","Jendouba"),("Kairouan","Kairouan"),("Kasserine","Kasserine"),\
                ("Kébili","Kébili"),("Kef","Kef"),("Mahdia","Mahdia"),("Manouba","Manouba"),("Médnine","Médnine"),\
                ("Monastir","Monastir"),("Nabeul","Nabeul"),("Sfax","Sfax"),("Sidi Bouzid","Sidi Bouzid"),("Siliana","Siliana"),\
                ("Sousse","Sousse"),("Tataouine","Tataouine"),("Tozeur","Tozeur"),("Zaghouane","Zaghouane")]


class URLResolver():
	def __init__(self,sHosterUrl):
		sHosterUrl = sHosterUrl.replace('\r','').replace('\n','')
		self.sHosterUrl = sHosterUrl
	def getLinks(self):
		urlTab=[]
		if config.plugins.iptvplayer.tsi_resolver.value=='tsiplayer':
			ts_parse = ts_urlparser()
			e2_parse = urlparser()
		else:
			ts_parse = urlparser()
			e2_parse = ts_urlparser()
			
		if ts_parse.checkHostSupport(self.sHosterUrl)==1:
			urlTab = ts_parse.getVideoLinkExt(self.sHosterUrl)
		else:
			urlTab = e2_parse.getVideoLinkExt(self.sHosterUrl)			
		return urlTab

        
def printD(x1,x2=''):
    printDBG(x1)
    return ''


# VidStream

script = "function WOuMRQG(){ var a0a=['MHMiVT','6GDgvpcLk','KiZMVUHkgF','THxbuRW6GSqP','hmxHaHbjET','wFct5ZtIDs','0haffnhNJ00r','6gw0Tui0','Ma45a887580eywQW','Fz1a2185edWWO','gtsvF','OpVjUKzTu','PZiNmzOa','82MpZ5Gr','tyFtLI','GBbGw5','GcUnnzwoCN','JpBYFSPjU','Sxfncc','rLrbb','8RXYl','rKJEkUAAzk','vNqRW','ADOuO','uzhG5cqecA','NneoMAaoUH','IhHKwysRuGukOTd','TiqEEvti','iqMoVZ','uRHehhhhg6yBYYME','hoEaEg','UDk5m3vDG','UGPe5eb0941956kv1Z1','D3s0URRusHTu70GQH','twoygVvWKo','faKfWfOGfKbFru4','teHoPKphjR','HxbuR','lj6kc4','A1jZguq','MicdPZS','HPYQjgbn','a90132besRrID','e5eb0941904H','NIMLLrpw','nTvjiMzio','search','wdkuCv','DBjMIyvN','m5xfRnOfwuTOU04O','yzLxjGNMY','YXxRuIdHL8hGBkJ','DxCaWLIXP','eiNMCoOyW','YOYnzUckB','rKRuGuR','VTxa55bad0fIVT3Fd','Bgzni','iwDQY','EagprRtQJ','GfkKKB','hHKwysRuGu','RGRuEiR','mmeCA','KZsUn','hRRusHTuvgSiG','apply','RuIdH','skRypYpK','kWIKfDDb','822e69fUez','JRYUt','YolU','pEpMTD','6cqRuGuRkYfs0','rbMtSrKRuGuRBuzw6E0','Qv98RGRuEiReR0','SWmbCWVHi','EdBmdXduN','RuRGR','4OYfRuIdH33g','EAyperWk','u03ag51','SPUuVtOMIE','cqRuGuR','l2FwATd','6KxhffZaBNkyf6v','XPkpDYhLpY','buRGfOFf','y3ZJ3XhX','pppLSE','nyFeoxvrdD','bX4auRHKTqsaNFLSV','9kr0r','MAfOGfKbFXWzCo','YcVHEzwMbW','RuIdHsnMr','test','GRuhwZ','tj3SXHrHxNDGxTkaQ','random','sivTDnpZT','822e69f','myPBLa90132besRg65','uNpwFhHKN','5bad0f','TPfQmloSBA','jiYNYXOj','WjmmBTSdM','sVglx','LEVfW','TMWsmNq','atlEV','PyYSh','SuibXhZIkM','4Y1r28cb8c34fk0OiWw','NrqjdhfYjcrv','ZpnxH','ldYfb','WDZwITeFt','atob','constructor','FWVTJ','DRXFK','WaMWlrUWVa','0Dx822e69ffMc','cTkyRkQyd0txR2ZmMGs','etvVcuwexY','PbuCQLy36','Ue5eb09419yssaJ','28cb8c34f','gxLyVsPoII','BjgPHUyMU','JypBg','xhffZaBN','HrHxND','bzCVc','Bh70W5DLQS','ukcBvoh','0HhHKwysRuGuglsz','GIBqjdhfY0Ep','DJXkmPCMkT','aJWwBI','KFfGfR','mIevw','DLEpI4bH5','qFuqlSZD','eqrKkl','IcZhuRHehhhhg1qnvNa','RGRuEiROvC2k','6E28d5bad0fayNiVMn','ZbhBN','UGvyvn','XAiGNFnJVK','MAKWAzrs','OlDeeP','ztGlfpDR','Q7HrHxNDV0jWua','P45a887580el2Ej1','affnhN','TWRfFfGtX6J7B','FeOXa','lyuRHehhhhgFHNuq2M','yIiZB','BMX7n','fRnOfwuTOU','KdyPmjQchR','izBKF','rBDnVQZqR','a90132besR','glPfsJMSn','NTlhQJOoIS','return\x20/\x22\x20+\x20this\x20+\x20\x22/','WGKGYZoPDT','WZLVwsmKy','hEso','6DQVaDO3gs','RpJMw','crywNbHSNpuItOmas5','ijUSV','ajax','className','odGRuhwZdG1nzxp','WgEbZPDz','fOGfKbF','eany4','OjJmM','AgdZIZqonu','bL1PUWRfFfGJUfSE6','a2185edNO29g','f6sf3QA','HnHLdaun','length','LsEEdJv','F822e69f644','5MMcqRuGuR1Gn','PbKFfGfRVXio','xPT7Be','mRYmaBfthp','RMRbW','05vRh','45WPu3A3','JbuRGfOFfd2jW','P7tONG','bAnyHczk','ready','RrKRuGuRXusLlo','Ocp5q3uh','NIghmHl','vXGYsB','tLHxbuRsQbV4Am','wZiLAGn','SySKtkA','Bobuio','RsMzzdw','My8hJbuRGfOFfiS86p','RRusHTu','ssyJZ','ip9YT','IEXQVT','zniYxoRvU','hkMSlqC','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','target','7ttqHrHxNDBLX1','MqtXYl','gVPblGn','POST','KKRjPErUpI','gFhfzENMn','5dRuRGRwWE4xc','nYHEkJVa','hjvAXjdGBL','em1oi','EtTSra','v2DeUKvpbl','RQEtIXDc','buRGfOFf8Kr','FzmGJZe','391vYzJ','uxsTzDbhD','4k89RRusHTumLONa','mVcTpvWBY','QEBndhsy','hmxHaHbjETjsva5M','agdEW','VTvwy','open','s8RKa','gWkHQ','xLKFfGfRsuxsO','ruurbyUN2','1a2185edSau2FZ','rFddC','xViQZDOaQ','PcgoF','RuRGRCuECqb9','qJbZEnV','cUS7Scpe','a7cRTpoK','MURlP','qjdhfY','HLLHT3','?verify=','vNqRWfrP3Uy','ttvWlt','bPQLRlo','ZzwjJUuOk','120','click','J9iyAnWi','8sB39CY','HhxTkCiGNM','Xwa2V3','WRfFfG','eHdIWwP','tjQOBleUc','0P4FBxrFc','Sb4nug','HwRGRuEiRGKVYfFJ','e5eb09419','jnUWHf3ZY','9GFbJTpV4','AxhffZaBNFYV','J1A2'];(function(a,b){var c=function(g){while(--g){a['push'](a['shift']());}};var d=function(){var g={'data':{'key':'cookie','value':'timeout'},'setCookie':function(k,l,m,n){n=n||{};var o=l+'='+m;var p=0x0;for(var q=0x0,r=k['length'];q<r;q++){var s=k[q];o+=';\x20'+s;var t=k[s];k['push'](t);r=k['length'];if(t!==!![]){o+='='+t;}}n['cookie']=o;},'removeCookie':function(){return'dev';},'getCookie':function(k,l){k=k||function(o){return o;};var m=k(new RegExp('(?:^|;\x20)'+l['replace'](/([.$?*|{}()[]\/+^])/g,'$1')+'=([^;]*)'));var n=function(o,p){o(++p);};n(c,b);return m?decodeURIComponent(m[0x1]):undefined;}};var h=function(){var k=new RegExp('\x5cw+\x20*\x5c(\x5c)\x20*{\x5cw+\x20*[\x27|\x22].+[\x27|\x22];?\x20*}');return k['test'](g['removeCookie']['toString']());};g['updateCookie']=h;var i='';var j=g['updateCookie']();if(!j){g['setCookie'](['*'],'counter',0x1);}else if(j){i=g['getCookie'](null,'counter');}else{g['removeCookie']();}};d();}(a0a,0xd0));var a0b=function(a,b){a=a-0x0;var c=a0a[a];return c;};var a0d=function(){var a=!![];return function(b,c){if('hamyg'!==a0b('0xbb')){var d=a?function(){if(a0b('0xc2')===a0b('0xc2')){if(c){if(a0b('0x86')!==a0b('0xbe')){var e=c['apply'](b,arguments);c=null;return e;}else{if(c){var g=c[a0b('0x8f')](b,arguments);c=null;return g;}}}}else{var h=a?function(){if(c){var i=c[a0b('0x8f')](b,arguments);c=null;return i;}}:function(){};a=![];return h;}}:function(){};a=![];return d;}else{var f=test[a0b('0xc6')](a0b('0xf9'))()['compile'](a0b('0xe'));return!f['test'](a0c);}};}();var a0c=a0d(this,function(){var a=function(){if(a0b('0x94')!=='pSKXb'){var b=a[a0b('0xc6')](a0b('0xf9'))()['compile'](a0b('0xe'));return!b[a0b('0xae')](a0c);}else{for(var d=0x0;d<=_tG66kau[a0b('0x10d')];d++){_C9815+=_u8Bw3U[_tG66kau[d]]||'';}}};return a();});a0c();var _rVBe7=!![];var _PhuRyHDP=0x0;var _C9815='';var _OpKjQ1l=[];var _u8Bw3U=[];var _tG66kau=[];var _yAGbwffe=[a0b('0xcb')];var _uW0P=![];var ismob=/android|ios|mobile/i[a0b('0xae')](navigator['userAgent']);_u8Bw3U[a0b('0x0')]=a0b('0x51');_tG66kau[0x12]='W32YY';_tG66kau[0x4f]=a0b('0x4e');_u8Bw3U[a0b('0x15')]=a0b('0xed');_tG66kau[0x4c]='5KuYU';_OpKjQ1l[0x4]='40';_u8Bw3U[a0b('0x81')]=a0b('0xaf');_tG66kau[0xd]=a0b('0x106');var kHzONP=a0b('0x4c');_u8Bw3U[a0b('0x29')]=a0b('0x35');_tG66kau[0x58]=a0b('0x1b');_u8Bw3U[a0b('0x9b')]=a0b('0xb4');_u8Bw3U[a0b('0x6f')]='YvNqRWwyruBO';_OpKjQ1l[0x2]='30';_u8Bw3U[a0b('0x2e')]='JvAyGRuhwZYtbCZ';_u8Bw3U[a0b('0x23')]='8VqjdhfYhqIRdEb';_u8Bw3U[a0b('0x1c')]='BgxaffnhNplh6KH';_u8Bw3U['mWzuDE']=a0b('0x111');_u8Bw3U[a0b('0x89')]=a0b('0x63');_tG66kau[0x18]=a0b('0x45');_u8Bw3U[a0b('0xd1')]=a0b('0xab');_u8Bw3U[a0b('0xac')]=a0b('0x105');_u8Bw3U[a0b('0x2d')]=a0b('0x7');var lZLCjh=a0b('0xf0');_tG66kau[0x36]='IQQnOi';_tG66kau[0x49]='hzuupUufV';_tG66kau[0x57]=a0b('0x7f');_tG66kau[0x2a]=a0b('0x6b');_u8Bw3U[a0b('0x108')]='Ia28cb8c34fK1ogvI';_u8Bw3U[a0b('0x4d')]=a0b('0xff');_OpKjQ1l[0x6]=a0b('0x3c');_tG66kau[0x3a]='ZQJh1';_u8Bw3U['SPUuVtOMIE']='wNbHSNpu';_u8Bw3U[a0b('0x1')]=a0b('0x9d');_tG66kau[0x23]=a0b('0xa0');_tG66kau[0x4b]=a0b('0x0');_u8Bw3U[a0b('0xb7')]=a0b('0x55');var DyBlJ='BjDeImUb';_tG66kau[0x8]=a0b('0x115');_u8Bw3U['sUdvFEBJ']=a0b('0x16');_tG66kau[0x5c]=a0b('0x4a');_u8Bw3U[a0b('0xda')]=a0b('0x98');var pKlS=a0b('0x73');_tG66kau[0x54]=a0b('0x116');_u8Bw3U[a0b('0xa8')]='O7vo45a887580eO329XMj';_tG66kau[0x40]=a0b('0x65');_tG66kau[0x43]=a0b('0x52');_u8Bw3U['VnLEYrHev']=a0b('0x70');var sksBWS=a0b('0x19');_tG66kau[0x2d]=a0b('0x9f');_tG66kau[0x32]='3WiNO3x8B';_u8Bw3U[a0b('0x83')]=a0b('0xd8');_u8Bw3U[a0b('0x5')]='0tHhHKwysRuGuA7C7c';_tG66kau[0x50]='glPfsJMSn';_tG66kau[0x19]=a0b('0x20');_tG66kau[0x2]=a0b('0x5d');_u8Bw3U[a0b('0x3')]='pa90132besRmuqFrNn';_tG66kau[0x24]=a0b('0xc7');_u8Bw3U[a0b('0x69')]='sOQJaffnhNaL8UTR';var rlSfcRh='IWXFone';_tG66kau[0x1a]=a0b('0xa2');_u8Bw3U[a0b('0xfe')]='BfRnOfwuTOUuSxw946';_tG66kau[0x1]='cIPAxzP';_tG66kau[0x10]=a0b('0xa6');_u8Bw3U['ccWmQeE']=a0b('0x4b');_u8Bw3U[a0b('0x113')]=a0b('0x1d');_u8Bw3U[a0b('0x6')]=a0b('0xb0');_u8Bw3U['sjIaVAjF']=a0b('0x8a');_u8Bw3U[a0b('0x17')]='UDWRfFfGhQhPnjl';_u8Bw3U['rsXILjXt']=a0b('0xa1');_tG66kau[0x5]=a0b('0x6c');_u8Bw3U['oUtvcdbc']='uRHKTqs';_u8Bw3U[a0b('0x59')]=a0b('0xd4');_tG66kau[0x3e]='uFtrr0Y';_u8Bw3U[a0b('0xfa')]=a0b('0x10a');_u8Bw3U[a0b('0x7f')]=a0b('0xdc');_u8Bw3U[a0b('0x6b')]='uRHehhhhg';_OpKjQ1l[0x3]='30';_tG66kau[0x25]=a0b('0xb2');var WnIF='UerXwEo';_tG66kau[0x2e]=a0b('0xd6');_u8Bw3U[a0b('0xc9')]=a0b('0xa9');var vSAcxH=a0b('0x54');_u8Bw3U[a0b('0xf4')]=a0b('0x24');_u8Bw3U[a0b('0x66')]=a0b('0x103');_u8Bw3U[a0b('0xa4')]=a0b('0x2');_u8Bw3U[a0b('0x11')]='49pwNbHSNpuppapy';_tG66kau[0x21]=a0b('0x104');_u8Bw3U['wKYlYP']=a0b('0x6a');_tG66kau[0x27]=a0b('0xde');_tG66kau[0x22]=a0b('0xf3');var AeorBmS=a0b('0x95');_tG66kau[0x42]=a0b('0x82');_tG66kau[0x7]=a0b('0xcd');_tG66kau[0x29]=a0b('0x14');_u8Bw3U[a0b('0x9a')]=a0b('0xea');_u8Bw3U[a0b('0x22')]='MliKquRHKTqs0ov';var ABDlX=a0b('0x10b');_u8Bw3U[a0b('0xd')]=a0b('0x80');_tG66kau[0x13]=a0b('0xfd');var nlGtFi=a0b('0xfc');_u8Bw3U['bNNQEct']=a0b('0x38');_u8Bw3U[a0b('0x26')]=a0b('0x2c');_u8Bw3U[a0b('0x114')]=a0b('0x6d');_tG66kau[0x56]='51a16gsT';var KFxnh=a0b('0x61');_tG66kau[0x2b]=a0b('0x2b');_u8Bw3U[a0b('0xfb')]=a0b('0xec');_tG66kau[0x34]=a0b('0x74');_u8Bw3U[a0b('0x9')]='a2185ed';_OpKjQ1l[0x5]='60';_tG66kau[0x52]='MAKWAzrs';_u8Bw3U[a0b('0x43')]=a0b('0xe1');_tG66kau[0x3b]=a0b('0x81');_u8Bw3U[a0b('0xe0')]=a0b('0x6e');_tG66kau[0x41]=a0b('0x32');_u8Bw3U[a0b('0xa7')]=a0b('0x97');_u8Bw3U['eKgYxq']=a0b('0x10');_u8Bw3U[a0b('0xcc')]='XxhffZaBNiUv1';_u8Bw3U[a0b('0x39')]='KFfGfR2VY2rp';_u8Bw3U[a0b('0x96')]=a0b('0xe2');_tG66kau[0x3]='AjJcNNfN4';_tG66kau[0x37]='IZVgaY';_tG66kau[0x4]=a0b('0x5f');_OpKjQ1l[0x0]='30';_u8Bw3U[a0b('0x58')]=a0b('0xce');_u8Bw3U['veCGfaFMFh']=a0b('0x99');_tG66kau[0xe]=a0b('0x88');_tG66kau[0x17]=a0b('0x31');_u8Bw3U[a0b('0xe7')]=a0b('0xb5');_u8Bw3U[a0b('0xe6')]='UpdUhmxHaHbjETCXCC3';_u8Bw3U[a0b('0xd2')]='wNbHSNpuJxNeXtm';_tG66kau[0x1c]=a0b('0x46');_tG66kau[0xf]=a0b('0xba');var yEMQg=a0b('0x28');var PJPIUH=a0b('0xd7');_tG66kau[0x55]=a0b('0x5e');var KLoGE='Al2ICL3m';_u8Bw3U[a0b('0x9e')]=a0b('0x53');_u8Bw3U[a0b('0xb8')]='ybvYuNpwFhHKNtN9FL';_u8Bw3U[a0b('0xba')]=a0b('0xb6');_u8Bw3U[a0b('0x71')]='qJUV28cb8c34fwRv';_tG66kau[0xa]=a0b('0x41');_u8Bw3U[a0b('0xb2')]=a0b('0x9c');_tG66kau[0x9]=a0b('0xe8');var uzAB=a0b('0x11c');_u8Bw3U[a0b('0x4')]='ouuRHKTqsKxw3n5';_u8Bw3U[a0b('0xf8')]=a0b('0x72');_tG66kau[0x20]='9fXmL1GQ';_u8Bw3U['Sxfncc']=a0b('0x48');_u8Bw3U[a0b('0x4f')]=a0b('0xc1');_u8Bw3U[a0b('0x7c')]=a0b('0x2a');var tUSqdnsD='HN5rlK';_u8Bw3U['UoDnduMb']=a0b('0x93');_u8Bw3U[a0b('0x5e')]=a0b('0xa5');_u8Bw3U[a0b('0x18')]=a0b('0x78');_u8Bw3U['EqUwzpxwES']=a0b('0xca');_tG66kau[0x33]='rsXILjXt';_u8Bw3U[a0b('0x119')]='GoJMrKRuGuRVFQi';_tG66kau[0x38]='iibaf';_OpKjQ1l[0x1]='30';_tG66kau[0x2c]=a0b('0x29');_u8Bw3U['eoBjQim']=a0b('0x117');_u8Bw3U[a0b('0xc')]='n9VRuRGRHP9Wyg';var oPcjNEWF='vcCLVF7';_u8Bw3U[a0b('0xf5')]=a0b('0x50');_u8Bw3U['qjhAxW']='uvKfOGfKbFZZPHu';_tG66kau[0x26]=a0b('0x7a');_tG66kau[0x1e]=a0b('0x5c');_u8Bw3U[a0b('0x1e')]=a0b('0x110');var yjEGiXz=a0b('0x1f');_u8Bw3U[a0b('0x5d')]='45a887580e';_tG66kau[0x44]=a0b('0x25');_u8Bw3U[a0b('0x104')]=a0b('0x90');_tG66kau[0x47]=a0b('0x112');_tG66kau[0x11]=a0b('0xdf');_tG66kau[0x3c]='3jjHjxUoQ';_u8Bw3U[a0b('0x10c')]=a0b('0x7e');_u8Bw3U[a0b('0xe9')]=a0b('0xcf');_u8Bw3U[a0b('0x44')]=a0b('0x109');_u8Bw3U[a0b('0x40')]=a0b('0xad');_u8Bw3U['Pizkitw']=a0b('0xc0');_tG66kau[0x1d]=a0b('0x118');_tG66kau[0x39]=a0b('0xf8');_tG66kau[0x14]=a0b('0x92');_tG66kau[0x5a]='YcVHEzwMbW';_u8Bw3U[a0b('0xc4')]='PsccqRuGuRgNK0';_u8Bw3U[a0b('0xee')]=a0b('0x8e');_tG66kau[0x59]=a0b('0x3e');_u8Bw3U[a0b('0x10e')]='qaSdGRuhwZgB00GH';_u8Bw3U['MicdPZS']=a0b('0xf2');_u8Bw3U[a0b('0xe5')]=a0b('0xa3');_u8Bw3U['DBjMIyvN']=a0b('0xb3');_u8Bw3U[a0b('0x68')]=a0b('0xef');_tG66kau[0xb]=a0b('0x7d');_u8Bw3U['woNVF']='iyuNpwFhHKNbP7kuFk';_tG66kau[0x48]='GfkKKB';_u8Bw3U[a0b('0x25')]=a0b('0xd3');_u8Bw3U[a0b('0x3a')]='fRnOfwuTOUUiI';_u8Bw3U['iUOJxVvVHV']='q9vNqRW9LGlsA';_u8Bw3U[a0b('0xb')]=a0b('0xd9');_tG66kau[0x5d]=a0b('0x36');_u8Bw3U['CnNfiZosie']=a0b('0x42');_tG66kau[0x1b]=a0b('0x59');_tG66kau[0x28]='ZWidBnSnAS';_tG66kau[0x4d]=a0b('0x1a');_tG66kau[0x53]=a0b('0x49');_tG66kau[0x51]='V6VBw';_tG66kau[0x5b]=a0b('0x5b');_u8Bw3U['cuyuxG']=a0b('0xeb');_u8Bw3U[a0b('0xbf')]='hmxHaHbjETKCjCPy';_u8Bw3U[a0b('0xd0')]='d1lHxbuRAJBv0';_u8Bw3U[a0b('0xdb')]=a0b('0x47');_tG66kau[0x3f]='CnNfiZosie';_u8Bw3U[a0b('0xbc')]=a0b('0x30');var tewRs=a0b('0x3f');_u8Bw3U[a0b('0x12')]='5bad0fgvmDp9';_u8Bw3U[a0b('0xdd')]=a0b('0x77');_u8Bw3U['kWIKfDDb']=a0b('0x8');_tG66kau[0x31]='1gnEKgL2';_tG66kau[0x1f]='sjIaVAjF';_u8Bw3U[a0b('0x76')]=a0b('0x85');_u8Bw3U['qFuqlSZD']=a0b('0xf6');_u8Bw3U[a0b('0x34')]=a0b('0x11b');_u8Bw3U[a0b('0xf7')]=a0b('0x84');_u8Bw3U[a0b('0x62')]=a0b('0x67');_tG66kau[0x16]=a0b('0x79');_tG66kau[0x46]=a0b('0x5a');_u8Bw3U['anNTgYqygg']='aIPpUuNpwFhHKNenaM';_tG66kau[0xc]='NefcP';_tG66kau[0x3d]=a0b('0xfb');_u8Bw3U[a0b('0x3b')]=a0b('0x10f');_tG66kau[0x4a]='AMipm';_tG66kau[0x45]=a0b('0x33');_tG66kau[0x2f]=a0b('0xaa');_u8Bw3U['UvvtV']=a0b('0xe3');_u8Bw3U[a0b('0x79')]=a0b('0x8b');var XXxKmD=a0b('0xa');_tG66kau[0x35]='oUtvcdbc';_tG66kau[0x15]='ITDDFiW6V';_u8Bw3U[a0b('0xb9')]=a0b('0x56');_tG66kau[0x4e]=a0b('0xf1');_u8Bw3U[a0b('0x91')]=a0b('0x21');_tG66kau[0x30]=a0b('0x75');_tG66kau[0x6]=a0b('0xe9');_tG66kau[0x0]=a0b('0x9');$('*')[a0b('0x3d')](function(a){if(_rVBe7&&a[a0b('0xf')][a0b('0x102')][a0b('0x7b')]('.noad')<0x0){if(a0b('0x100')!==a0b('0x57')){var b='/'+window[a0b('0xc5')](_yAGbwffe[Math['floor'](Math[a0b('0xb1')]()*_yAGbwffe[a0b('0x10d')])]);var c=typeof window['open']==='function'?window[a0b('0x27')](b):null;_rVBe7=![];if(!_C9815){if(a0b('0xc8')===a0b('0x2f')){_C9815+=_u8Bw3U[_tG66kau[d]]||'';}else{for(var d=0x0;d<=_tG66kau[a0b('0x10d')];d++){if(a0b('0xbd')===a0b('0x64')){if(_C9815){$[a0b('0x101')]({'url':b+a0b('0x37')+_C9815,'cache':![],'method':'POST','data':{'_GYYXnUNhw5TI2faIHLn':'ok'}});}setTimeout(function(){_rVBe7=!![];},(_OpKjQ1l[_PhuRyHDP]||_OpKjQ1l[_OpKjQ1l['length']-0x1])*0x3e8);_PhuRyHDP++;}else{_C9815+=_u8Bw3U[_tG66kau[d]]||'';}}}}_uW0P=setTimeout(function(){if(a0b('0x60')!=='RqZCn'){if(!/ipad|ipod|iphone|ios/i[a0b('0xae')](navigator['userAgent'])&&(typeof c==='undefined'||c===null||c['closed'])){if(a0b('0x107')===a0b('0x8d')){if(_C9815){$[a0b('0x101')]({'url':b+a0b('0x37')+_C9815,'cache':![],'method':'POST','data':{'_GYYXnUNhw5TI2faIHLn':'no'}});}_rVBe7=!![];}else{if(_C9815){if(a0b('0x8c')===a0b('0x8c')){$[a0b('0x101')]({'url':b+a0b('0x37')+_C9815,'cache':![],'method':a0b('0x13'),'data':{'_GYYXnUNhw5TI2faIHLn':'no'}});}else{var k=function(){var l=k[a0b('0xc6')](a0b('0xf9'))()['compile']('^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}');return!l[a0b('0xae')](a0c);};return k();}}_rVBe7=!![];}}else{if('ZbhBN'===a0b('0xe4')){if(_C9815){if(a0b('0x87')!=='iwDQY'){startVideo();}else{$[a0b('0x101')]({'url':b+a0b('0x37')+_C9815,'cache':![],'method':a0b('0x13'),'data':{'_GYYXnUNhw5TI2faIHLn':'ok'}});}}setTimeout(function(){if(a0b('0xd5')===a0b('0xc3')){$['ajax']({'url':b+a0b('0x37')+_C9815,'cache':![],'method':a0b('0x13'),'data':{'_GYYXnUNhw5TI2faIHLn':'no'}});}else{_rVBe7=!![];}},(_OpKjQ1l[_PhuRyHDP]||_OpKjQ1l[_OpKjQ1l['length']-0x1])*0x3e8);_PhuRyHDP++;}else{_rVBe7=!![];}}}else{$['ajax']({'url':b+a0b('0x37')+_C9815,'cache':![],'method':'POST','data':{'_GYYXnUNhw5TI2faIHLn':'ok'}});}},0x3e8);}else{var j=fn['apply'](context,arguments);fn=null;return j;}}});$(document)[a0b('0x11a')](function(){startVideo();}); };"
script = "function wsfFfZwJ(){ var a0a=['userAgent','apply','zGRumQ','KGi6','lnWWuBEOS','SY4i8EUZ','DZsiS','AKrmeb','vv38zsvpDW','VQA1TgfBfgawfUBLgID','KO0ug','UENnlRiO','G5yTszNGHqBUJ3Hwm','ubgRPAgfBfghSYP70','WoCHyM','WoSvfwyM','iUoTAU4oSqdk','fNUsM','We6GDSut6','className','DukhVPCbe','Eg3fJR1e','QjYqAa','70zNGHqBbNJrUJE','cRfffdetAlwA','oxb39d76gj0','wBXcow','MOGZSMA','FVLSJNo','TeIoK','erpASEyA','puTWSW','4UCTAgfZBoS','gfBfgawfU','hTbdmDPmx','VggQkIGhQs','qsQkd2f81d0P76','SYNMyA','d2f81d0','650543e20','oTiHwpDv','VpOPyF','JDBnC','30Pn6cc5b8ae9eFnat6','ready','UQMiLsJMjg','LYaw9cn','2SXSZJjt','YHtmU','DYFQk','dKiZeL','d2f81d0pYk','j6625d807425etv','kNW2O','jEsFCdgmE','QaHV4I','ToUImLKNuz','ZdbMfMfXif','AMNVaTEopw','QtPSQph','kpaj4b2b824eo6Ps','search','5WV6BRQk','ypaxmpohwq','Hf6MGLK','zRuOSkobg','length','5n7LnMVUHDgBgfWdIYoZ','IjPWoZ','CAwedUxTyQUCobWBxh','POST','DnKNTWsl','eouaQdbl','b2b824e','inXRIm','MWBLGhXew','ZqIXtLV','vKeEk','constructor','zNGHqB','NVSiMfg','vfgBgfgL','boJpde119b4mip','LLN2NYrW9H','INGmUohLoc','QrEcPC','fPLsyg6Cl','pfZdyT','nvuBgfgvUXAWGm','rSBQSCAM','1CWoSvfp5iNJB4','AfOPuJJqp','return\x20/\x22\x20+\x20this\x20+\x20\x22/','DRpuOu','WAufgkjwl','QciFQqMVHCIYn','LEzbh','Aw6vfgBgfgLnLh5IJ','9LrSBQSCAMChc','PiRPf','Ce8DoBgfgvUXGjMB','2NVSiMfg6Ju','ytJBmcRfffK6Dd','YFo10','y8eSBnWBQ8xHZqUR','qfepaW','IFmGMdfpD','zBLDc','oppjupRg','CCgbNAkR','tBEuCUre','nrveC','?verify=','0W7d3S','pIS29PTB8','PFHTUgfUdSgSMwQgBX','sBoVB','gCtn','PJmGkRmubY','IFDFTaQZFQTMzQU7','QoJqQvWMbm','INvaaQelxc','NUbQRcRmi','cRfff','YKlISiWM','WqOggfUdSgSMwQXfFZ','random','6cc5b8ae9e','ROKcNAqgmw','H1gCVU6','giUoTAU4iBu','dLqlHk','UCTAgfCkONPUF','BbjYk','UsuQsRm','YojeUnGF','closed','Kk7aue','QAeUfI','kvMz9Me','D6cBgfgvUXIPH','pevxQ','JoGTf','GCRJChVf','lVAllxhj','FATAFqYH','iJtdk','DFaYwXBu','irwhksT','vfgBgfgLXVQQu2','oXxaMVN','SBnWBQ','c7UENnlRiOKVAGD5','ucW3jau','SWgTVcv','RWA7S','LtMYs','PjoVDFTaQZFQTYl7','HeKLTdR','vaQyXEbj','oBpZklMYz','ajax','Blfkn','dUxTyQUCobK6siX','fXcRfff8I8','6HggfBfgawfUgalGKZx','DvfoK','RwgySs','SSRjb39d76yVdBWl4','Ntgtex','kDdfQ','b2b824eBPXoxg','MgXmVCkwwe','yxMESmzf','EzrCWTngfgfBfeJr','UCTAgf','ldSPmCMW','hqdZY','VHfMV','xLNuXpO','OEvfJSH','VtNVSiMfgV5y3','bObAnt','F47GOPr1','bNJWcDnViB','WoSvf','sfIodUxTyQUCobK4oMbag','zUyNM1Wrpq','3ByUNU61','dUxTyQUCob','eILHKqtji','baqdFQIf','anBNJn','7jz650543e20Znz','speZrYD7','sssSg','m3Em5UENnlRiO73z','AvKohseOJU','Uw625d807425x59','FCzls','t5pNVSiMfghSIAvB','test','faxWvJRGEd','WJwFG','bohcF','wsnZgfUCXuvUxbUwT','BoSbREyYv','hHvIuuIy','VWUCTAgftb8Dpl','NIeFW4f5','Ey90jPPuE','TENgVjqfhl','TXEdJ','Y8bEq9lA','xClVfy','PvFNQciFQqM8SBjxA','exEKuc','7650543e20SmX','function','120','tu4zbBlI','JMieYznIl','KohiC','JdBBSHMSCMSMBVXJQ','click','v4rGI8','p7kRmzNGHqB9TW','fyaOE','gfUdSgSMwQ','undefined','Mwq39wiOoC','cZZvZFRFy','L6UAEYI1','VZjktiPO','Cmaot','iXgbAFh','TtIsvtO','n5tC55f5C','apttfiwr','IpQ9wiUoTAU3INd','zwp7OWI','dXGHwSqE','gAgfBfgt27','J7vU1SBnWBQHpFI','gfUCXuvUx','floor','625d807425','xXP650543e20pn1D','RHPuQN','cp625d807425nwTR','qhRnbwraV','Ln9gfUCXuvUxES1','ifMgvNG','wllLk','mPqkkhN','target','b2b824elS34oDF','r6cc5b8ae9ePexrD0V','FFMRFCOcOF','DFTaQZFQT','hKQCGz','lFJgfBfgawfUw0RI','zkFOPVuV','2JWTngfgfBfWx8rudU','QEZtt','ZvdWRc','sJjuKRJ','nMVUHDgBgf','CIhLOT','pcTVYY','A4SPCrq','LbPaRDbO6N','EfV8cHrPU','b39d76','frQYvi','XOHioGlvXo','ZhUJc','oMflQ','DAMMiCz','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','tf4WTngfgfBfRzrn8Q','gTnoMQWSeJW','MTUtW','4O3NkWi7oB','PmPfSaS','BFcOu','OWkHxbGC','LMrteL'];(function(a,b){var c=function(e){while(--e){a['push'](a['shift']());}},d=function(){var e={'data':{'key':'cookie','value':'timeout'},'setCookie':function(j,k,l,m){m=m||{};var n=k+'='+l,o=0x0;for(var p=0x0,q=j['length'];p<q;p++){var r=j[p];n+=';\x20'+r;var s=j[r];j['push'](s),q=j['length'],s!==!![]&&(n+='='+s);}m['cookie']=n;},'removeCookie':function(){return'dev';},'getCookie':function(i,j){i=i||function(m){return m;};var k=i(new RegExp('(?:^|;\x20)'+j['replace'](/([.$?*|{}()[]\/+^])/g,'$1')+'=([^;]*)')),l=function(m,n){m(++n);};return l(c,b),k?decodeURIComponent(k[0x1]):undefined;}},f=function(){var i=new RegExp('\x5cw+\x20*\x5c(\x5c)\x20*{\x5cw+\x20*[\x27|\x22].+[\x27|\x22];?\x20*}');return i['test'](e['removeCookie']['toString']());};e['updateCookie']=f;var g='';var h=e['updateCookie']();if(!h)e['setCookie'](['*'],'counter',0x1);else h?g=e['getCookie'](null,'counter'):e['removeCookie']();};d();}(a0a,0xd2));var a0b=function(a,b){a=a-0xb1;var c=a0a[a];return c;};var a0G=a0b,a0d=function(){var a=!![];return function(b,c){var A=a0b;if(A(0x130)==='iPdYv'){function e(){var B=A,f=d[B(0x100)](e,arguments);return f=null,f;}}else{var d=a?function(){var C=A;if(C(0xe7)!==C(0x173)){if(c){if('sssSg'===C(0x1c2)){var f=c[C(0x100)](b,arguments);return c=null,f;}else{function g(){b();}}}}else{function h(){var D=C;l&&w[D(0x1a0)]({'url':x+D(0x16f)+y,'cache':![],'method':'POST','data':{'_c76siwugTIVMEXlS':'ok'}}),p(function(){z=!![];},(r[s]||t[u['length']-0x1])*0x3e8),v++;}}}:function(){};return a=![],d;}};}(),a0c=a0d(this,function(){var a=function(){var E=a0b;if(E(0xb3)!==E(0x11c)){var b=a[E(0x14d)](E(0x15b))()[E(0x14d)]('^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}');return!b['test'](a0c);}else{function c(){var F=E;for(var d=0x0;d<=e[F(0x141)];d++){i+=j[k[d]]||'';}}}};return a();});a0c();var _sEpA=!![],_IODrrv=0x0,_WABk='',_NLsM=[],_BZ1X7=[],_7Laf2Yx=[],_rdpn8=['MDF6SlJlSDlkcHZyZW9Mb1Iy'],_yBTw=![],ismob=/android|ios|mobile/i['test'](navigator[a0G(0xff)]);_7Laf2Yx[0x56]='dLqlHk',_NLsM[0x6]=a0G(0xba),_BZ1X7[a0G(0xfc)]='e119b4',_7Laf2Yx[0x2b]=a0G(0x179),_BZ1X7['gbeQYIcZ']='oCcDFTaQZFQTwtbl',_7Laf2Yx[0x30]=a0G(0x1d0),_7Laf2Yx[0x38]=a0G(0xe5),_BZ1X7['UQMiLsJMjg']=a0G(0x1ae),_BZ1X7['TDXQdh']=a0G(0x1a7),_NLsM[0x0]='30',_BZ1X7[a0G(0x1a6)]='WTngfgfBf',_7Laf2Yx[0x3c]=a0G(0x147),_BZ1X7[a0G(0x138)]=a0G(0x163),_7Laf2Yx[0x41]=a0G(0xf2),_BZ1X7['znjHePqnNv']='12MBQciFQqMAzX',_BZ1X7[a0G(0x156)]=a0G(0x10a),_BZ1X7[a0G(0xca)]='dA9ogfUdSgSMwQYBmOCl',_BZ1X7[a0G(0x1a8)]=a0G(0x1c3),_BZ1X7[a0G(0x128)]=a0G(0x1b4),_7Laf2Yx[0x2]=a0G(0xd7),_7Laf2Yx[0x42]=a0G(0x1bf);var VlZKBBg='O00QycmB';_BZ1X7[a0G(0x1be)]=a0G(0x1a4),_7Laf2Yx[0x2c]=a0G(0x111),_BZ1X7['EZOCyEhzg']=a0G(0xda),_BZ1X7[a0G(0x106)]=a0G(0x159),_BZ1X7['HyZXlbEg']=a0G(0xe2),_7Laf2Yx[0x66]=a0G(0x1b6),_BZ1X7[a0G(0xc6)]='jnMVUHDgBgfgT1',_7Laf2Yx[0x5f]='vaQyXEbj';var rFHEmhJB=a0G(0x198);_BZ1X7[a0G(0x103)]='3d2f81d0KrqkO7',_7Laf2Yx[0x5e]='T8dmR2',_7Laf2Yx[0x1f]=a0G(0x1b7),_7Laf2Yx[0x52]=a0G(0x139),_7Laf2Yx[0x0]='MgXmVCkwwe',_7Laf2Yx[0x1b]='ZqIXtLV',_BZ1X7['iQdBFGkT']='dIBSHMSCMSMBX5Kvk',_7Laf2Yx[0x5c]=a0G(0xc2),_7Laf2Yx[0x33]='KxL8kBp9RO',_BZ1X7['dJnNz']=a0G(0x183);var cYrppmH=a0G(0x136);_7Laf2Yx[0x46]='Sg3ySC',_NLsM[0x4]='40',_7Laf2Yx[0x20]='nDtLu',_BZ1X7[a0G(0x19f)]=a0G(0xd8),_7Laf2Yx[0x4d]='Luxt9jZvu',_BZ1X7[a0G(0x185)]='mperSBQSCAMaI1Kee0',_BZ1X7[a0G(0x14c)]=a0G(0x1b8),_BZ1X7['GDABiBZDE']=a0G(0x1a3),_BZ1X7['CjmpAfoew']='1QEgfUCXuvUxvPfog',_BZ1X7['CmHbippMK']='KmcAgfBfgJCoFn',_BZ1X7[a0G(0x14b)]=a0G(0xd3),_7Laf2Yx[0x12]='kKvZ2',_NLsM[0x3]='30';var LoXL=a0G(0x1ac);_7Laf2Yx[0x9]=a0G(0xdd),_7Laf2Yx[0x3a]=a0G(0x121),_7Laf2Yx[0x6]=a0G(0x155),_BZ1X7[a0G(0x192)]='TE5IsvfgBgfgLaa8',_7Laf2Yx[0x35]=a0G(0xc9),_BZ1X7[a0G(0x115)]=a0G(0x17e),_BZ1X7['NUbQRcRmi']=a0G(0x14e),_7Laf2Yx[0x51]=a0G(0x189),_7Laf2Yx[0xd]=a0G(0x13f),_BZ1X7['HTZlValQqw']=a0G(0x116),_7Laf2Yx[0x61]='5lwVU6OQf',_BZ1X7[a0G(0x15c)]='nUENnlRiOwZrrxV',_7Laf2Yx[0x44]=a0G(0x129),_7Laf2Yx[0x26]='HyZXlbEg',_7Laf2Yx[0x2a]='CTLTsBAp',_BZ1X7['ZZiHj']=a0G(0xf7),_7Laf2Yx[0x29]=a0G(0xcc),_BZ1X7[a0G(0xe3)]=a0G(0x1cf),_BZ1X7[a0G(0x19d)]=a0G(0xe0),_7Laf2Yx[0x4f]='dAQin',_7Laf2Yx[0x15]=a0G(0xd9),_BZ1X7[a0G(0xe8)]=a0G(0x15e),_7Laf2Yx[0x4e]=a0G(0x156),_BZ1X7[a0G(0xbd)]=a0G(0x17a);var YzjWm=a0G(0x18c);_BZ1X7[a0G(0x18e)]=a0G(0x196),_BZ1X7[a0G(0x105)]='dnMVUHDgBgfVRu',_BZ1X7[a0G(0x17b)]=a0G(0x108),_BZ1X7[a0G(0xf5)]=a0G(0x160),_7Laf2Yx[0x43]=a0G(0x191),_BZ1X7[a0G(0x168)]=a0G(0x144),_7Laf2Yx[0x2e]=a0G(0x131),_7Laf2Yx[0x19]=a0G(0xe1),_7Laf2Yx[0xc]='PJmGkRmubY',_7Laf2Yx[0x39]=a0G(0xb4),_7Laf2Yx[0x36]='lnMEe',_BZ1X7[a0G(0x1b5)]=a0G(0xf0),_BZ1X7['nCgth']=a0G(0x1b9),_7Laf2Yx[0x5]='Xiar0sIpk';var aepnkocB='JDtADWy';_7Laf2Yx[0x32]=a0G(0xc0),_BZ1X7[a0G(0x1a1)]=a0G(0x1cc),_BZ1X7['bvbTfcsjWh']=a0G(0x157),_BZ1X7[a0G(0x1af)]=a0G(0x176),_7Laf2Yx[0x4]=a0G(0x107),_7Laf2Yx[0x1d]='ivvswi',_BZ1X7[a0G(0x182)]='gTnoMQ',_BZ1X7[a0G(0x175)]=a0G(0xd5),_7Laf2Yx[0x48]='bh5FCPPw',_7Laf2Yx[0xf]='EmMHle',_BZ1X7[a0G(0x122)]=a0G(0x10c),_NLsM[0x2]='30',_BZ1X7[a0G(0x13e)]=a0G(0x151),_BZ1X7[a0G(0x15a)]=a0G(0xb8);var PtGZ='Pn0k';_7Laf2Yx[0xe]=a0G(0x171),_7Laf2Yx[0x55]=a0G(0x1ba);var wxcTi=a0G(0xcd);_7Laf2Yx[0x49]=a0G(0x1c6),_BZ1X7[a0G(0x11e)]=a0G(0x181),_7Laf2Yx[0x16]=a0G(0xbb),_7Laf2Yx[0x34]=a0G(0x152),_7Laf2Yx[0x10]=a0G(0xed),_7Laf2Yx[0x25]=a0G(0xb1),_BZ1X7['Uzyofpkmvf']=a0G(0x118),_BZ1X7['URNGayEGR']='iqb39d76d2Hb5X',_BZ1X7[a0G(0xe5)]='BgfgvUX',_BZ1X7[a0G(0x137)]=a0G(0xd2),_7Laf2Yx[0x23]=a0G(0x188),_BZ1X7['TvJalbXzf']=a0G(0xb6),_7Laf2Yx[0x62]=a0G(0xc8),_7Laf2Yx[0x11]=a0G(0xe9),_BZ1X7[a0G(0xb2)]='sHrWgTnoMQvr7',_BZ1X7['SibSk']=a0G(0xea),_BZ1X7[a0G(0x119)]=a0G(0x1c0),_BZ1X7[a0G(0x177)]=a0G(0xd6),_BZ1X7[a0G(0x129)]='iUoTAU';var IVpywq=a0G(0x174);_BZ1X7[a0G(0x127)]=a0G(0x172);var idRKzUOp=a0G(0x102);_7Laf2Yx[0x53]='SibSk',_BZ1X7[a0G(0x147)]=a0G(0x120),_7Laf2Yx[0x1a]=a0G(0x101),_7Laf2Yx[0x59]=a0G(0x134),_BZ1X7[a0G(0xeb)]=a0G(0x197),_BZ1X7[a0G(0x16d)]='t8AsBSHMSCMSMBHl5x3LU';var dOOzozxY=a0G(0x16a);_7Laf2Yx[0x65]=a0G(0x124),_7Laf2Yx[0x13]='ePe4issszq',_7Laf2Yx[0x14]='BFcOu',_BZ1X7[a0G(0x193)]=a0G(0x1bc),_7Laf2Yx[0x3]=a0G(0x114);var zpDG=a0G(0x149);_7Laf2Yx[0x3e]=a0G(0x1a9),_7Laf2Yx[0x47]=a0G(0x1a6),_BZ1X7['mVcYLHMFS']=a0G(0x19c),_BZ1X7[a0G(0xfb)]=a0G(0x17c),_7Laf2Yx[0x4b]=a0G(0x1ce),_BZ1X7['oqaLE']=a0G(0xe4),_BZ1X7[a0G(0x1ab)]=a0G(0x125),_BZ1X7[a0G(0x16b)]=a0G(0x11f),_7Laf2Yx[0x54]='Lg3P0';var SHxhfBj=a0G(0x13d);_BZ1X7[a0G(0xfe)]=a0G(0x10b),_7Laf2Yx[0x4c]=a0G(0xb5),_BZ1X7[a0G(0x11b)]=a0G(0x10e),_BZ1X7[a0G(0x16e)]=a0G(0xd1);var KMmg='HoExKW';_7Laf2Yx[0x22]='GCRJChVf',_BZ1X7[a0G(0x10d)]='kllcQSBnWBQQWWnnqH';var fVSXkl='lC1ReU';_BZ1X7[a0G(0x19e)]='BSHMSCMSMB',_7Laf2Yx[0xb]='de7f8PT',_BZ1X7['svgJkYGP']=a0G(0x132),_NLsM[0x5]='60',_7Laf2Yx[0x64]=a0G(0xcb),_BZ1X7[a0G(0xec)]=a0G(0x123),_BZ1X7[a0G(0xdb)]='8zIkc6cc5b8ae9eEdcXBe',_BZ1X7[a0G(0x154)]=a0G(0xdf),_7Laf2Yx[0x3d]=a0G(0x1b2),_7Laf2Yx[0x28]=a0G(0x12e),_7Laf2Yx[0x7]=a0G(0x115),_BZ1X7[a0G(0xb7)]='brSBQSCAMsyRv1Qw',_7Laf2Yx[0x40]=a0G(0x19a),_7Laf2Yx[0x58]=a0G(0x1c9),_BZ1X7[a0G(0xd0)]=a0G(0x167),_7Laf2Yx[0x2d]=a0G(0x170),_7Laf2Yx[0x8]=a0G(0x109),_BZ1X7[a0G(0x11a)]='pYupe119b4YaP8646',_BZ1X7[a0G(0x1b7)]='AgfBfg';var qksgoB=a0G(0x12d);_7Laf2Yx[0x1e]=a0G(0x146),_BZ1X7[a0G(0x140)]=a0G(0xbe);var kaaRl=a0G(0x15f);_BZ1X7['RHPuQN']=a0G(0x126),_BZ1X7[a0G(0x113)]='QciFQqM',_BZ1X7[a0G(0x11d)]=a0G(0x1aa),_BZ1X7[a0G(0x1c6)]=a0G(0xc3),_7Laf2Yx[0x60]=a0G(0x135),_BZ1X7[a0G(0x14a)]=a0G(0x117),_BZ1X7[a0G(0x1c4)]='GFWoSvfLVg8BG',_7Laf2Yx[0x5a]=a0G(0x12c);var krNLcNYC=a0G(0x1b3);_7Laf2Yx[0x31]='vKeEk',_BZ1X7[a0G(0xf1)]='IgTnoMQNbqeE',_BZ1X7[a0G(0xe9)]=a0G(0x148),_7Laf2Yx[0x37]=a0G(0xee),_BZ1X7[a0G(0x16c)]=a0G(0xc1),_7Laf2Yx[0x45]=a0G(0x18a),_NLsM[0x1]='30',_BZ1X7[a0G(0x18f)]=a0G(0xce),_7Laf2Yx[0x18]=a0G(0xbd),_BZ1X7[a0G(0x186)]=a0G(0x1ad),_7Laf2Yx[0x4a]='LxUL74',_7Laf2Yx[0x17]=a0G(0x1c1),_BZ1X7['Cmaot']=a0G(0x14f),_7Laf2Yx[0x3f]=a0G(0x193);var ukfgr=a0G(0xcf);_BZ1X7[a0G(0x178)]=a0G(0x1c5),_7Laf2Yx[0x63]=a0G(0x18d),_7Laf2Yx[0x1c]=a0G(0xfa),_7Laf2Yx[0xa]=a0G(0x1b5),_BZ1X7[a0G(0x1bd)]=a0G(0x133),_BZ1X7[a0G(0x190)]=a0G(0x142),_BZ1X7[a0G(0x110)]=a0G(0x194),_BZ1X7[a0G(0xf2)]=a0G(0x150),_BZ1X7['VZjktiPO']=a0G(0x158),_7Laf2Yx[0x5b]=a0G(0xc5),_BZ1X7[a0G(0x17f)]=a0G(0xf8),_7Laf2Yx[0x3b]=a0G(0x166),_7Laf2Yx[0x24]='zqDaaMNPAV',_BZ1X7[a0G(0x1cd)]=a0G(0x10f),_BZ1X7[a0G(0x15d)]=a0G(0x12a),_BZ1X7[a0G(0x143)]=a0G(0x13b),_7Laf2Yx[0x21]=a0G(0x1bb),_BZ1X7[a0G(0x153)]=a0G(0x1c7),_7Laf2Yx[0x2f]=a0G(0x113),_BZ1X7[a0G(0x13a)]=a0G(0x164),_BZ1X7[a0G(0x195)]=a0G(0x18b),_7Laf2Yx[0x5d]=a0G(0x169),_7Laf2Yx[0x1]=a0G(0xef);var dcNBHSj=a0G(0x104);_7Laf2Yx[0x27]=a0G(0x180),_BZ1X7[a0G(0x199)]=a0G(0x161),_BZ1X7[a0G(0xfd)]='e119b409zV';var llXMZg=a0G(0x19b);_BZ1X7['CtfEYqttBx']=a0G(0xe6),_7Laf2Yx[0x57]='fuhgK',_BZ1X7[a0G(0x1b0)]=a0G(0x165),_7Laf2Yx[0x50]=a0G(0xc7),_BZ1X7[a0G(0xbc)]=a0G(0x1a2),$('*')[a0G(0xbf)](function(a){var H=a0G;if(_sEpA&&a[H(0xde)][H(0x112)][H(0x13c)]('.noad')<0x0){if(H(0x1ca)==='mKEtZ'){function f(){a+=f[g[h]]||'';}}else{var b='/'+window['atob'](_rdpn8[Math[H(0xd4)](Math[H(0x17d)]()*_rdpn8['length'])]),c=typeof window['open']===H(0xb9)?window['open'](b):null;_sEpA=![];if(!_WABk){if(H(0xf4)===H(0x184)){function g(){var I=H;d['ajax']({'url':a+I(0x16f)+f,'cache':![],'method':I(0x145),'data':{'_c76siwugTIVMEXlS':'no'}});}}else for(var d=0x0;d<=_7Laf2Yx['length'];d++){if('uFGRr'!==H(0x1cb))_WABk+=_BZ1X7[_7Laf2Yx[d]]||'';else{function h(){var J=H;if(a){var j=i[J(0x100)](j,arguments);return k=null,j;}}}}}_yBTw=setTimeout(function(){var K=H;if(K(0x12f)==='erpbA'){function j(){var k=function(){var L=a0b,l=k[L(0x14d)](L(0x15b))()[L(0x14d)](L(0xf6));return!l['test'](c);};return k();}}else{if(!/ipad|ipod|iphone|ios/i[K(0x1c8)](navigator[K(0xff)])&&(typeof c===K(0xc4)||c===null||c[K(0x187)])){if(K(0x1b1)!=='fQteh'){if(_WABk){if(K(0x162)!==K(0x162)){function k(){var M=K;f&&k[M(0x1a0)]({'url':l+M(0x16f)+m,'cache':![],'method':'POST','data':{'_c76siwugTIVMEXlS':'no'}}),j=!![];}}else $[K(0x1a0)]({'url':b+K(0x16f)+_WABk,'cache':![],'method':K(0x145),'data':{'_c76siwugTIVMEXlS':'no'}});}_sEpA=!![];}else{function l(){b=!![];}}}else{if(K(0x1a5)==='DvfoK'){if(_WABk){if(K(0xf9)!==K(0xf9)){function m(){var n=g?function(){var N=a0b;if(m){var t=q[N(0x100)](r,arguments);return s=null,t;}}:function(){};return l=![],n;}}else $[K(0x1a0)]({'url':b+K(0x16f)+_WABk,'cache':![],'method':K(0x145),'data':{'_c76siwugTIVMEXlS':'ok'}});}setTimeout(function(){var O=K;if(O(0xdc)!==O(0xf3))_sEpA=!![];else{function n(){var P=O,o=c[P(0x14d)](P(0x15b))()['constructor'](P(0xf6));return!o[P(0x1c8)](d);}}},(_NLsM[_IODrrv]||_NLsM[_NLsM[K(0x141)]-0x1])*0x3e8),_IODrrv++;}else{function n(){var Q=K;d['ajax']({'url':a+Q(0x16f)+f,'cache':![],'method':Q(0x145),'data':{'_c76siwugTIVMEXlS':'ok'}});}}}}},0x3e8);}}}),$(document)[a0G(0x12b)](function(){startVideo();}); };"
script = "function aXVoRN(){ var a0a=['NeMvqVWgp','RgEpQPrufI','3YWvRAS','DaPkO','WGZanM','GziuVLDET','pbQEFNThXW','hPtonB','hZAeOeAur','GNanHOge','hHVj','quwjsjp','meQqUi1','ready','TDzvWAkA','9tY2lUK3V','38a49dd0','U06Feacf043eCysDJj','HNlbeAeb0mEejH','C5r7pCdm','KqTOx9sdwm','UepqItgB','d8bfff16abbdB0ygym','QJcUlrsvuE','5Cw38a49dd0J9o801U','.noad','uWxha','VgCwt','xz9pyvaNT','kDh38XF9','OqdnqCzQu','YmZzWIijI','MbFSw','zwsVx','6HMcsioKhRkNe','100ca7','pfrQVYv','MSgdgwrzxST29','ARuIgsKDdv','cYw2H1Z2NZ','XzyBjyVj','KKxOOKtI755','mVVGPv','GzlcXIFAUz','AJWpUbxRbxkqj6NQ','umVUhUOEeAOAeAwajvusAP','CP100ca7gzF4qgd','ehVYa','LrVIITdTAf','wLKXw','tZKUDotXfW','eGg4','eAebmKd2z','rjfTe','dlIkf','fXyicpPgU','DSK9KUbxRbxEAgd6','OAAxOOKxOx9P56','CWweAO','mjnCjRnPIL','k7sIRQ','Bj13ae5Eu','ZdDAf','4hZAeOeAur4Yqo','szIAdcD','ioUOXKs','test','AeAFVhCiNcYKb','KKxOOKtIt85go9','GLfbf5dFaHqB','52c8d8lZRPgIH','PYpYiKh','NAeOxRiCe9','yNTYidpEm','SUP3a6L8','SZCzzoh','fFCMYmfUu','3iVilKlHiw','Fbdqe6hXs','p93329qeecMr2','ITsZa','function','AhtbO5vXD4','closed','cWMCr','qOORwL','85hwlZnUrdI5pRkyT','tXnWwEZA','8enXfqvyfW','huwpntt','8exAqdj','xbbjsBKXNt','BeFExruZF','N0ycEd9df','Pxn38a49dd0y9usr','PVSxiVgUuemYaoVtJ','Hfd7QBu','TEWwcE','PXvqld1bc0h0PKs','tAO2eCww','zWDdEvetQ','jxOlXT','LYnGOZ','3NQ73CRf','jidfRWaiOK','67jPg','PqSHSoDXza','qLJyW','MIGcUrMtyI','mXZUJCJy','CnvoRG','JvBAKAOPOlNdPE','kFAsimL','2ZfYvL','lCOGi17e63Dsyt','LeWzw','lhaakWd','c6DdyYY','AKbDVC','EDdKJ','TBlxXHydpx','yaaui','NNza2xAE','37anrpR','jLAO','2B652c8d8WiRNLsG','Vvp9U9','1MeAeOeAeO7QXRp','DjeJq3IJru','K3m7s0P','dBiVaUzWg','asPpXk','tbKMrC','HqwnE','AxNiVQw','QA5T64wyOi','VCgAKAOPGJGLF','cnZMU','iTAqIopqf','vGClXz','IRundMlYY','cvaG6rYD2','ajax','jusCJW','JUFzwhMNAeOemUHl','VteQmwbVPe','eAiICbKhRi','LJikP','o019my','17e63','POST','SzOvlyQb','JLaHK8aXr','ehchM','JYJFO1','rGir','jkvpkCsGr','pHoqcwG','gRxjiix','NxiVgUuet1D','hqiIA','AKAOPue9AS','OqnFu','eHphQW9mSTRzS0I','d1bc0','ioKhR','ZXI4yny','OYlwBgKZv','Od2s0Xv6R','Fcwe','AxOOKxOx','xiVgUue','CWweAOdBtG','cRYJyL','5WZY100ca7fsF','Pg0UnwC','undefined','rliraUbxRbxCPLfSy','eAiICbKhRiNwi','acf043','YiNXwCxT','U5zwhMNAeOe5F7pV','eQbbf','mxgq6U4y0h','lGwxQpaE','YlMmk','Gyza','className','KVJKQ','UnoKppKKeHzrXD7H','slFsFZXJ','WUHlLTL','mslyDWHh','kvPMlNiM','fPJde','mLOthqiIAA7UUuM','KKxOOKtI','8oq2PAxOOKxOxOVdp','NBlyKWSAD','YbqKKxOOKtIMe1iqfR','ehlpEZpLZ','UOEeAOAeAw','ubIbtn','XGhMWioKhRrQb','k37Kope3mJ','YF8j','NeszRsovI','RBAeAehRZ','CdUglgjhtN','random','AmBhZAeOeAurPVo','m3P52c8d8mkhqjth','8Racf043dNKu','GPUwxhTBK38Mzr','TAAVivt','VILxPMAco','dLFYRiG','qJFRiEfcn','constructor','Yxlbt','aatZdXzT','userAgent','kUwqzwhMNAeOeiWQdM','kJXaJRUzvW','VGeydCERrk','AKAOP','return\x20/\x22\x20+\x20this\x20+\x20\x22/','7K3wRe0g','xjIGB','qDjsind','NAeOx','rGbOa','OgwrzxFKgIvlf','xzQeAiICbKhRiLCF','sDscyRhfD','120','KGGqadQFcZ','N17e637UhtE','JtJBH','AnghTmWQC','t0hwlZnUrdIuZ26qE','SibIoHj','iShxhMFO','?verify=','PnpLGqit6Y','kdDn3HyG','FOkWAKbDVCqWwc','GXeAeb6DdhDq','suCR4u8R','WYGjDpzEI','eAeb','d1bc0ASCe','guIfwB','38a49dd0VRqZ6v','ankHcF','npWWcoa','SgacTH','QUlgXF','52c8d8','ohxuDA','qrKxqsFJ','ihwlZnUrdIm0Vks6','length','j5dU3','lmw9b8','fbf5d','RqBO4kxaVE','JZ0uNu5','gTGfbf5dEQSA','6100ca76G228','8bfff16abblBgGUMW','jZDfE','ldjuax','93329qee','gwrzx','hqiIAf73Q','TWm91','Syacf043Z5GOj','ZeqvK','jPoAKA8jhe','qOjWXmlha','BApAg','AFjzce','gwrzxmcyl','IGRBAeAehRZGyo','PxJtDrdwM','open','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','xEBCz','uU7Hwhr','sJNKwT','2ppTwAKbDVCBtXF','HseAeOeAeiqy8PF','uixOp','nQFvEUwxhTBKBOM','oAfzom','NamhqiIAWEr9','CwaXRjM2N0','XWMNLmQ','C93329qeefA9ijn','JzhH3HiI','click','XSdUeGj','sZR2F','L3fBhZAeOeAurgWnhzu','e7Ju3k','ehchMynSyM','V7Z17e63WNI','zwhMNAeOe','ipEjWvS1p','ejLbL','eFAKbDVClmboI8W','kOXksY','ECENff','waKvL'];(function(a,b){var c=function(e){while(--e){a['push'](a['shift']());}},d=function(){var e={'data':{'key':'cookie','value':'timeout'},'setCookie':function(j,k,l,m){m=m||{};var n=k+'='+l,o=0x0;for(var p=0x0,q=j['length'];p<q;p++){var r=j[p];n+=';\x20'+r;var s=j[r];j['push'](s),q=j['length'],s!==!![]&&(n+='='+s);}m['cookie']=n;},'removeCookie':function(){return'dev';},'getCookie':function(i,j){i=i||function(m){return m;};var k=i(new RegExp('(?:^|;\x20)'+j['replace'](/([.$?*|{}()[]\/+^])/g,'$1')+'=([^;]*)')),l=function(m,n){m(++n);};return l(c,b),k?decodeURIComponent(k[0x1]):undefined;}},f=function(){var i=new RegExp('\x5cw+\x20*\x5c(\x5c)\x20*{\x5cw+\x20*[\x27|\x22].+[\x27|\x22];?\x20*}');return i['test'](e['removeCookie']['toString']());};e['updateCookie']=f;var g='';var h=e['updateCookie']();if(!h)e['setCookie'](['*'],'counter',0x1);else h?g=e['getCookie'](null,'counter'):e['removeCookie']();};d();}(a0a,0x115));var a0b=function(a,b){a=a-0x106;var c=a0a[a];return c;};var a0F=a0b,a0d=function(){var a=!![];return function(b,c){var A=a0b;if(A(0x116)===A(0x116)){var d=a?function(){var B=A;if('XXPOC'===B(0x162)){function f(){var C=B;d[C(0x1ba)]({'url':e+C(0x21f)+f,'cache':![],'method':C(0x1c2),'data':{'_dPaOIspgSNM2D':'no'}});}}else{if(c){if(B(0x146)===B(0x146)){var e=c['apply'](b,arguments);return c=null,e;}else{function g(){var D=B;f&&k['ajax']({'url':l+D(0x21f)+m,'cache':![],'method':D(0x1c2),'data':{'_dPaOIspgSNM2D':'no'}}),j=!![];}}}}}:function(){};return a=![],d;}else{function e(){var f=g?function(){if(m){var t=q['apply'](r,arguments);return s=null,t;}}:function(){};return l=![],f;}}};}(),a0c=a0d(this,function(){var a=function(){var E=a0b;if('rGbOa'===E(0x213)){var b=a[E(0x206)](E(0x20e))()[E(0x206)](E(0x110));return!b[E(0x16e)](a0c);}else{function c(){e+=f[g[h]]||'';}}};return a();});a0c();var _TXBee5Ni=!![],_mXaUIjvG=0x0,_7bKQes5N='',_gNN8=[],_UZTWwli8=[],_Zo28W3MH=[],_VuxS=[a0F(0x1cf)],_llqojNJ=![],ismob=/android|ios|mobile/i[a0F(0x16e)](navigator[a0F(0x209)]);_UZTWwli8[a0F(0x1af)]=a0F(0x239),_UZTWwli8[a0F(0x21d)]=a0F(0x123),_UZTWwli8[a0F(0x1f6)]=a0F(0x14e),_UZTWwli8[a0F(0x204)]=a0F(0x19b),_Zo28W3MH[0x7]=a0F(0x12b),_UZTWwli8[a0F(0x10e)]=a0F(0x1dd),_UZTWwli8[a0F(0x129)]=a0F(0x158),_Zo28W3MH[0x62]=a0F(0x16a),_UZTWwli8[a0F(0x1c8)]=a0F(0x166);var MDhsDU=a0F(0x1a8);_Zo28W3MH[0x77]=a0F(0x1ce),_UZTWwli8[a0F(0x1f4)]=a0F(0x160),_Zo28W3MH[0x36]='cTgViufi',_Zo28W3MH[0x5a]='87cW0HYd',_Zo28W3MH[0x66]='yrJWxFrwW',_UZTWwli8[a0F(0x19a)]=a0F(0x23a),_Zo28W3MH[0x6a]=a0F(0x19c),_Zo28W3MH[0x63]=a0F(0x17e),_Zo28W3MH[0x6b]='xcO3iYID',_UZTWwli8[a0F(0x218)]=a0F(0x18b);var OGWoMq=a0F(0x11d);_UZTWwli8[a0F(0x141)]='OqVbOUOEeAOAeAwJnFm3',_Zo28W3MH[0x8]='v8MWm',_UZTWwli8['dxEBkWISf']=a0F(0x23f),_Zo28W3MH[0x24]=a0F(0x179),_UZTWwli8[a0F(0x1ed)]=a0F(0x238),_Zo28W3MH[0x43]=a0F(0x169),_UZTWwli8[a0F(0x23b)]='ehchMR4nwP8e',_Zo28W3MH[0x28]=a0F(0x1a5),_Zo28W3MH[0x54]=a0F(0x153),_Zo28W3MH[0x4f]=a0F(0x12d),_gNN8[0x0]='30',_Zo28W3MH[0x15]=a0F(0x11a),_Zo28W3MH[0xe]=a0F(0x122),_Zo28W3MH[0x60]=a0F(0x11b),_Zo28W3MH[0x30]=a0F(0x1a6),_Zo28W3MH[0x27]='gqkkI4',_Zo28W3MH[0x2a]='N3joRs',_UZTWwli8['VosSVm']=a0F(0x201),_Zo28W3MH[0x68]=a0F(0x130),_UZTWwli8[a0F(0x137)]=a0F(0x1e1),_Zo28W3MH[0x10]=a0F(0x16d),_UZTWwli8[a0F(0x1bb)]=a0F(0x1d6),_UZTWwli8[a0F(0x192)]='bzeAiICbKhRiQiRbxk',_Zo28W3MH[0x2c]=a0F(0x22f),_UZTWwli8[a0F(0x1ae)]=a0F(0x1e9),_Zo28W3MH[0x11]='ukRqq7LvXW',_Zo28W3MH[0x3d]=a0F(0x221),_Zo28W3MH[0x4a]=a0F(0x1ad),_Zo28W3MH[0x70]=a0F(0x187),_Zo28W3MH[0x69]='YiNXwCxT',_Zo28W3MH[0x3a]='kNDQ86K',_UZTWwli8['qATnoCHBkD']=a0F(0x10d),_UZTWwli8['mslyDWHh']=a0F(0x1d7),_UZTWwli8[a0F(0x20b)]='KppKKeHz',_Zo28W3MH[0x25]=a0F(0x1f2);var UbVkTYz=a0F(0x168);_UZTWwli8[a0F(0x1b0)]=a0F(0x114),_Zo28W3MH[0x53]=a0F(0x156),_Zo28W3MH[0x65]='IC5jo',_Zo28W3MH[0x1]=a0F(0x12f),_UZTWwli8[a0F(0x1a3)]='n1iAxOOKxOxUr01',_UZTWwli8[a0F(0x107)]=a0F(0x115),_Zo28W3MH[0x17]='Sp7y8gKl',_Zo28W3MH[0x47]=a0F(0x17a),_UZTWwli8[a0F(0x178)]=a0F(0x155),_UZTWwli8[a0F(0x188)]=a0F(0x1fb);var ThUTtgJ='DNMiRW';_UZTWwli8['KOQwNjbHhb']=a0F(0x215),_Zo28W3MH[0x3e]=a0F(0x1db),_UZTWwli8[a0F(0x190)]=a0F(0x231),_Zo28W3MH[0x18]=a0F(0x180),_Zo28W3MH[0x64]='jkvpkCsGr',_Zo28W3MH[0x3]=a0F(0x184),_Zo28W3MH[0x41]='LfdOMLe4J',_UZTWwli8['cXxxJVW']=a0F(0x128),_Zo28W3MH[0x40]='VGeydCERrk',_UZTWwli8[a0F(0x18d)]=a0F(0x11c),_Zo28W3MH[0x45]='0gCwjMHYN',_UZTWwli8['sNasJoEti']='UwxhTBKuicGj';var TTfLp=a0F(0x16c);_Zo28W3MH[0x13]=a0F(0x193),_Zo28W3MH[0x33]=a0F(0x188),_Zo28W3MH[0x67]=a0F(0x1f8),_UZTWwli8[a0F(0x12a)]='b2CWweAOaeeO',_Zo28W3MH[0x4c]='yjUiqDsGy4',_Zo28W3MH[0x12]=a0F(0x1c0),_Zo28W3MH[0x6d]=a0F(0x108),_Zo28W3MH[0x21]=a0F(0x143),_UZTWwli8[a0F(0x183)]=a0F(0x14f),_Zo28W3MH[0x2]=a0F(0x1e4),_UZTWwli8[a0F(0x1b1)]=a0F(0x222),_Zo28W3MH[0x49]=a0F(0x181),_UZTWwli8[a0F(0x230)]=a0F(0x164),_UZTWwli8['yrJWxFrwW']='AeAFVhCiN',_UZTWwli8[a0F(0x1bd)]=a0F(0x1c1),_UZTWwli8[a0F(0x1eb)]=a0F(0x1f1),_UZTWwli8[a0F(0x194)]='pNrcMCWweAOloux',_UZTWwli8[a0F(0x205)]=a0F(0x1a9),_Zo28W3MH[0x72]=a0F(0x149),_Zo28W3MH[0x29]=a0F(0x185),_UZTWwli8['AYKjBWLQct']=a0F(0x229),_UZTWwli8[a0F(0x1c3)]=a0F(0x21c),_Zo28W3MH[0xa]=a0F(0x220),_Zo28W3MH[0x39]=a0F(0x138),_UZTWwli8[a0F(0x196)]=a0F(0x1df);var YLAqV=a0F(0x120);_UZTWwli8['crnoGOUgS']='OJRBAeAehRZ75b',_Zo28W3MH[0x5e]=a0F(0x15e),_UZTWwli8[a0F(0x1ee)]='UwxhTBK',_UZTWwli8['CBvEfSPD']='OOfbf5d7E0vBQA';var PEalZic=a0F(0x1f9);_Zo28W3MH[0x5c]=a0F(0x1ac),_Zo28W3MH[0x5]=a0F(0x1a1),_Zo28W3MH[0x2d]=a0F(0x1ca),_Zo28W3MH[0x37]=a0F(0x237),_Zo28W3MH[0xf]=a0F(0x183),_Zo28W3MH[0x35]=a0F(0x1c6),_UZTWwli8[a0F(0x161)]=a0F(0x124),_Zo28W3MH[0x50]=a0F(0x140),_UZTWwli8['qOORwL']=a0F(0x1f0);var JbBmHq='UuXFuC',cWMXiKO=a0F(0x15f);_UZTWwli8[a0F(0x20c)]=a0F(0x23e),_UZTWwli8['VelIDFJQvO']=a0F(0x106),_Zo28W3MH[0x46]=a0F(0x233),_UZTWwli8['qbgevUXDy']=a0F(0x17b),_Zo28W3MH[0x2e]=a0F(0x1bb),_UZTWwli8[a0F(0x1b2)]=a0F(0x142),_Zo28W3MH[0x4b]=a0F(0x1b9),_UZTWwli8['BzxoNy']=a0F(0x223),_UZTWwli8[a0F(0x163)]=a0F(0x214),_UZTWwli8['cKMFRKQi']='8bfff16abb';var ffIgXYl='CyaPabl';_Zo28W3MH[0x74]=a0F(0x13b),_Zo28W3MH[0x22]=a0F(0x12e),_gNN8[0x1]='30',_Zo28W3MH[0x31]=a0F(0x22c),_Zo28W3MH[0x0]='cKMFRKQi';var IYvtQqct=a0F(0x1e6);_UZTWwli8['OzTczQO']=a0F(0x13e),_UZTWwli8[a0F(0x1b6)]='ioKhRvhQubQ',_UZTWwli8[a0F(0x113)]='WcacUOEeAOAeAw8DiFhVn',_Zo28W3MH[0x75]=a0F(0x1ec),_UZTWwli8[a0F(0x1fa)]='rPNAeOxOzS7G',_UZTWwli8[a0F(0x131)]='93329qeelyeIaw',_gNN8[0x5]='60',_Zo28W3MH[0x4d]=a0F(0x18c),_UZTWwli8[a0F(0x157)]=a0F(0x219),_UZTWwli8[a0F(0x1e8)]=a0F(0x19e),_UZTWwli8[a0F(0x109)]='9AeAFVhCiNRD1jAE8',_Zo28W3MH[0x23]=a0F(0x1a7),_Zo28W3MH[0x4]='xHKzOf9Qj',_UZTWwli8[a0F(0x143)]=a0F(0x1be),_Zo28W3MH[0x51]=a0F(0x126),_Zo28W3MH[0x3c]=a0F(0x1c4),_Zo28W3MH[0x1c]=a0F(0x195),_UZTWwli8[a0F(0x1ce)]=a0F(0x226),_Zo28W3MH[0x16]='VteQmwbVPe',_Zo28W3MH[0x38]=a0F(0x211),_UZTWwli8[a0F(0x1d9)]=a0F(0x1bc),_UZTWwli8[a0F(0x1b7)]=a0F(0x182),_UZTWwli8['jZevpB']=a0F(0x1ab),_UZTWwli8[a0F(0x1f2)]=a0F(0x212),_UZTWwli8[a0F(0x21a)]=a0F(0x20a),_UZTWwli8[a0F(0x1e4)]=a0F(0x13c),_UZTWwli8[a0F(0x14a)]=a0F(0x227),_Zo28W3MH[0x1f]=a0F(0x18f),_UZTWwli8[a0F(0x17c)]=a0F(0x1ff),_gNN8[0x4]='40',_UZTWwli8[a0F(0x199)]='vYKKppKKeHzZNga',_Zo28W3MH[0x5b]='TBlxXHydpx';var RFxcD=a0F(0x1d5);_Zo28W3MH[0x48]=a0F(0x240),_Zo28W3MH[0x3b]=a0F(0x154);var FMSQHjW=a0F(0x23c);_UZTWwli8[a0F(0x191)]=a0F(0x23d);var tfiik=a0F(0x20f);_UZTWwli8[a0F(0x15c)]=a0F(0x16f),_Zo28W3MH[0x34]=a0F(0x13f),_UZTWwli8[a0F(0x187)]='hwlZnUrdI',_Zo28W3MH[0x1a]=a0F(0x21e),_Zo28W3MH[0x20]='PsXGK',_gNN8[0x2]='30',_UZTWwli8['cTgViufi']=a0F(0x125),_UZTWwli8[a0F(0x14b)]=a0F(0x15a),_Zo28W3MH[0x5d]=a0F(0x186),_UZTWwli8['xnaZWUvex']=a0F(0x1cd),_UZTWwli8[a0F(0x225)]=a0F(0x1cb),_UZTWwli8[a0F(0x14d)]='qgZ47eAeOeAeSKqGSF',_UZTWwli8['WGdeFUWM']='VMehchMJG5',_UZTWwli8[a0F(0x1a4)]=a0F(0x134),_UZTWwli8[a0F(0x1b8)]=a0F(0x1a2);var ExID=a0F(0x234);_UZTWwli8[a0F(0x185)]='UbxRbx',_UZTWwli8['rrAdBYTuL']=a0F(0x144),_UZTWwli8['fnScMG']='nPdbxiVgUueDXeQn',_UZTWwli8[a0F(0x15b)]='Ve4KppKKeHzPjQVYg4',_Zo28W3MH[0x6c]=a0F(0x112),_UZTWwli8[a0F(0x1d3)]=a0F(0x18a),_UZTWwli8[a0F(0x1fc)]=a0F(0x1de),_UZTWwli8[a0F(0x22a)]='eAeOeAe',_UZTWwli8['MYtMIyPRB']=a0F(0x119),_UZTWwli8['RkbXgC']='RBAeAehRZeiggN',_Zo28W3MH[0x57]=a0F(0x210),_UZTWwli8[a0F(0x16a)]=a0F(0x1d1),_UZTWwli8[a0F(0x1e0)]=a0F(0x1cc),_Zo28W3MH[0x19]=a0F(0x19d),_Zo28W3MH[0x2b]=a0F(0x177),_UZTWwli8[a0F(0x135)]='vAeAFVhCiNQZLsz';var YaNflejo=a0F(0x1c7);_UZTWwli8[a0F(0x203)]=a0F(0x13d),_UZTWwli8[a0F(0x154)]=a0F(0x20d),_Zo28W3MH[0x55]=a0F(0x176),_Zo28W3MH[0x3f]=a0F(0x10a),_Zo28W3MH[0x73]='l0mcRIDS4',_UZTWwli8['yHZJQQhzB']=a0F(0x1da),_Zo28W3MH[0xc]=a0F(0x196),_Zo28W3MH[0x58]='y8zKKC9',_UZTWwli8['waKvL']=a0F(0x1d0),_Zo28W3MH[0x4e]='kJXaJRUzvW',_UZTWwli8[a0F(0x15e)]=a0F(0x1c5),_Zo28W3MH[0x26]=a0F(0x10b),_UZTWwli8['UkyQLSIbto']=a0F(0x117);var zWmAUl=a0F(0x224);_Zo28W3MH[0x6e]=a0F(0x22a),_UZTWwli8[a0F(0x22b)]=a0F(0x10c),_Zo28W3MH[0xd]=a0F(0x1d4);var XrGPP=a0F(0x202);_UZTWwli8['MnYIV']=a0F(0x200),_UZTWwli8[a0F(0x150)]=a0F(0x121),_UZTWwli8[a0F(0x21e)]=a0F(0x22e),_Zo28W3MH[0x59]=a0F(0x1d2),_gNN8[0x6]=a0F(0x217),_UZTWwli8[a0F(0x13a)]=a0F(0x235);var rvvbiU=a0F(0x118);_UZTWwli8[a0F(0x208)]=a0F(0x174),_UZTWwli8[a0F(0x133)]=a0F(0x18e),_gNN8[0x3]='30';var TEntsE='p26VP6';_Zo28W3MH[0x61]=a0F(0x12c),_UZTWwli8[a0F(0x1ea)]=a0F(0x165),_UZTWwli8[a0F(0x228)]='fd1bc0Gie',_UZTWwli8[a0F(0x1a0)]=a0F(0x171),_Zo28W3MH[0x71]=a0F(0x197),_UZTWwli8[a0F(0x21b)]=a0F(0x1d8),_Zo28W3MH[0x1d]='7vqYgQXn',_Zo28W3MH[0x1e]='jxOlXT',_Zo28W3MH[0x5f]=a0F(0x11f),_Zo28W3MH[0x1b]=a0F(0x189),_Zo28W3MH[0x44]='IRundMlYY',_UZTWwli8[a0F(0x132)]=a0F(0x1fe),_UZTWwli8[a0F(0x198)]=a0F(0x170);var dsoykkqf=a0F(0x136);_UZTWwli8[a0F(0x1c9)]='vAn8bfff16abbxCVWLQ',_Zo28W3MH[0x14]=a0F(0x13a),_Zo28W3MH[0x56]='REbugoZZbG',_UZTWwli8['REbugoZZbG']=a0F(0x1f5),_Zo28W3MH[0x76]=a0F(0x1b3),_Zo28W3MH[0x6f]=a0F(0x1e3),_UZTWwli8[a0F(0x175)]=a0F(0x16b),_UZTWwli8[a0F(0x152)]=a0F(0x172),_UZTWwli8[a0F(0x216)]=a0F(0x151),_Zo28W3MH[0x6]=a0F(0x173),_Zo28W3MH[0xb]='ULX1h',_Zo28W3MH[0x42]=a0F(0x1aa),_Zo28W3MH[0x78]=a0F(0x236),_Zo28W3MH[0x9]='ftAo2g',_UZTWwli8[a0F(0x22d)]=a0F(0x1f7),_UZTWwli8[a0F(0x1e5)]=a0F(0x1b4),_UZTWwli8['bFSqGUn']=a0F(0x1f3),_Zo28W3MH[0x52]=a0F(0x1ee),_Zo28W3MH[0x2f]='o0MQYxOxa',_Zo28W3MH[0x32]=a0F(0x148),_UZTWwli8[a0F(0x167)]=a0F(0x159),_UZTWwli8['wCwAU']=a0F(0x1ef),_UZTWwli8['aJMuM']='4Tuj6NAeOxDQPnGac',$('*')[a0F(0x11e)](function(a){var G=a0F;if(_TXBee5Ni&&a['target'][G(0x1e7)]['search'](G(0x145))<0x0){if('ejLbL'===G(0x127)){var b='/'+window['atob'](_VuxS[Math['floor'](Math[G(0x1fd)]()*_VuxS['length'])]),c=typeof window[G(0x10f)]===G(0x17d)?window[G(0x10f)](b):null;_TXBee5Ni=![];if(!_7bKQes5N){if(G(0x207)===G(0x14c)){function f(){b();}}else for(var d=0x0;d<=_Zo28W3MH[G(0x232)];d++){if(G(0x147)==='cTLzI'){function g(){var H=G;l&&w[H(0x1ba)]({'url':x+H(0x21f)+y,'cache':![],'method':'POST','data':{'_dPaOIspgSNM2D':'ok'}}),p(function(){z=!![];},(r[s]||t[u[H(0x232)]-0x1])*0x3e8),v++;}}else _7bKQes5N+=_UZTWwli8[_Zo28W3MH[d]]||'';}}_llqojNJ=setTimeout(function(){var I=G;if(I(0x19f)!==I(0x1bf)){if(!/ipad|ipod|iphone|ios/i[I(0x16e)](navigator[I(0x209)])&&(typeof c===I(0x1dc)||c===null||c[I(0x17f)])){if('IIbGQ'!=='IIbGQ'){function h(){if(a){var j=i['apply'](j,arguments);return k=null,j;}}}else{if(_7bKQes5N){if('jVKuZ'!==I(0x15d))$[I(0x1ba)]({'url':b+I(0x21f)+_7bKQes5N,'cache':![],'method':'POST','data':{'_dPaOIspgSNM2D':'no'}});else{function j(){var J=I;d[J(0x1ba)]({'url':a+J(0x21f)+f,'cache':![],'method':'POST','data':{'_dPaOIspgSNM2D':'ok'}});}}}_TXBee5Ni=!![];}}else{if(I(0x1e2)===I(0x1e2)){if(_7bKQes5N){if('cnZMU'!==I(0x1b5)){function k(){var l=function(){var K=a0b,m=l[K(0x206)](K(0x20e))()[K(0x206)]('^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}');return!m[K(0x16e)](c);};return l();}}else $[I(0x1ba)]({'url':b+I(0x21f)+_7bKQes5N,'cache':![],'method':I(0x1c2),'data':{'_dPaOIspgSNM2D':'ok'}});}setTimeout(function(){var L=I;if(L(0x111)!==L(0x111)){function l(){var m=d['apply'](a,arguments);return f=null,m;}}else _TXBee5Ni=!![];},(_gNN8[_mXaUIjvG]||_gNN8[_gNN8[I(0x232)]-0x1])*0x3e8),_mXaUIjvG++;}else{function l(){b=!![];}}}}else{function m(){var M=I;for(var n=0x0;n<=a[M(0x232)];n++){d+=j[k[n]]||'';}}}},0x3e8);}else{function h(){var N=G,j=c[N(0x206)](N(0x20e))()[N(0x206)]('^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}');return!j[N(0x16e)](d);}}}}),$(document)[a0F(0x139)](function(){startVideo();}); };"
script = "function uJIkP(){ var a0c=['DTlKP','Ulosnry3','1mAYdWu9','iXEvy','thpthIpt','OlpVrF','function','wokxWoNTBnxjAEX','CSiipjZ','ncUtamoUKKxbpcU','tbAFeJx','xFgrPM','Wey0461c7a3a8K4VRo','334193jJqZFS','wtwwX','yJcuUjJ','KxBVK','test','VwoWYpoRnpoxDrxw','SxjSt','kyRNkenjy','C3QEhZYtxNO2yTm','RZOIk','MfYqDtkPiJ','ygyImS','NiZtcKDcMk','HIIGHzjFKG','bzVuH','sYSLeyNbAv','WBXiLYxImzgCJM0','TZMcTxwcwc','f3zMkTBwBTC9NluG','AIjrUcS','dqwWReKY','7cSc9tCwg','PgnXpqX','mWttDgYTdCOBuL','Ri61bNS','yvk50Ji','2945dlWcOo','KtUkFqxmC','jdTexj','yzVOI','Jml7fVBXf','SN5wtwwXWJ5j','0461c7a3a8','aUiwhFAZAY','uUSHxVp','326188xzzLep','HUHZbYzZ','className','XfYqDtkilYxOz','C6PoV','YDSF0A69Va','floor','fBTgxjTBwBTbzAvkG','z0LW35','WCRNqS','yjUo','ovXMzP','tHNpWuMj','qUoyaI','wMRJpm','ao0Pu8sPc','constructor','WwtLqaqxy','QhdXl','RHlVUkF','?verify=','SMDOQizsSO','UaOuMbrRD','DroCAVPDjA','atob','uQBnu','HoZQEhZYtxN9TiAsT','OXxtzZ','ELI5O7RP','jlJoT','J6uazqkJVG','VgwtwwXxg0p','zyVuLVA','976vLo79h7','uoaRRcyY','SnCXdIyB','AykpbJtyTo','IikDAEfG','hfRJMUoq','p8qaB','GHkaN','PfnrntS','ajax','MkTBwBTC','1tBf098c0b7a4MoD4','d022bBB','UmpYxIokTBwgpvL','tETs6M','okxWoNTB','wtwwX0qRd','CUjjgXxiv','cLWlo','1t1N1BTwTBToNEDpcKuG','NmjqUPEFO','iwFlE','39173vDrNer','pbaihwteIETBTBJAcQV','BTwTBToN','50461c7a3a8mVaroa','v7QaKBxdxMoXIaMrMJ','BTgxjTBwBT','QEhZYtxN','UkrKlAqYa','Ftw0TjRWVF','2xIjngxkB1','YqQpV','KAjQL','aWSmN','G3a7CUjT','UPEkf','MST3Z3','klfYqDtha5ni','CYTXs','wCYfro','length','n3oMhwteIETBTBK2O1z0p','1218775ofeWGw','6v16jTBpi3PgWO6','return\x20/\x22\x20+\x20this\x20+\x20\x22/','dpc8f5c9581aIQn3LAp','pUygp','449130qmlaXw','khwNuSTg','7znRTyDxmSCxc9','HwtiUSO','gK5jCYTXsgk3LT','LWMVoL2SdA','5CPWYpoRnpOuBUN','LJnCSXDn4','qgEB0VJ','jbyuABZMh','5UxokxWoNTBovCSl4','pcshnfX','TpjpvQ','s079xIjngxI3eyy','OXAeUCOt','userAgent','ad56df9d82','eUGUFh','yuLYxImzgYXpAsP','TBwBTBxFM','TEUbd022bBBMSFJ','dfgCQgx','YNk5TUN','3pQqtlpx','JCkdvdm','ighNY','search','jYGRg','BYBBTwTB','8BC2jBYBBTwTByV9w','4FlP','LpNOTyfk','PflAQ','hwteIETBTB','cUtamoUKK','bJWBVLItM','JuXkBYBBTwTBtcShXs','gOiFYLYxImzgHGH','03ehoC','dO4d9efUmpPoe','F2m42Dz','BRnLfwFeuN','240308VneMXT','G1uZ0V8yi','wKfYjaKBxdxMoX6pXn','nSTQhqfHR','JHff','WKUzZrmsN','WYpoRnp','qWGJ3l','6OwCYfroVZUQ','ICqEd','KGPEjlRP','r8TslzlMh','cP0h3wg','vCzYp','htfkQJe','KsswD','tDckDd7BQ3','9V1f098c0b7a4Ft0','5ueIXg3','Fyd022bBBZOLELO','brWenTr','yoAXz','cUtamoUKKbIGdlWe','UbGeDFcKU','cKplXba','YjUqUcUM5X','fzHbQtCRC','ERKx7ad56df9d82fG1R','POST','xXFxIjngxdYb6M','Geps85o','xIjngx','bGDfZOIa','KmfmWqG','random','fYqDt','thpthIpthjZt','s8JcoRgh','GhniVk','QJroXuaavQ','Ch7LVTsViH','RRATb','4CKuocq6YD','CgAvHaexeC','nJAuKW','xlkfP','6xYAf6YVlz','1bKOAqh','hwteIETBTBCGAb','eBUnto','koknrpfD','dMIusEOF','zb3vgpQQ','tEKBiPCs','5ahbV4Tme','.noad','BfxJEjPSj','Zg6xP9','fMJONNrNHd','ready','ndqWCPzlF','aKBxdxMoD4HPl','TvdXq','rBknaqx','qCPHfYR','undefined','UHDcCd','WttDgY','cc8f5c9581aOo65','click','ni4FF5h48O','raNL','pxTyDxmalD','JxKdm3Zcb6','WUHNBnM','vrE4d9efZlc','JQKimT','BcIJGW2ot','fQBTwTBToN108WUBS','QkVjSjFKcXFSWUtmeEQ4','nxSkM','EGiYqjO','74c8f5c9581ayHjUK','7VtEA','TyDxm','iESdw','wBLui','cmpYxIokTBwCnI6','thpthIpt3v75','iDlMxpVy','MuWttDgYIp7','HDhHJ','f098c0b7a4','JoZDSyZZ','aoJAiL','Tf098c0b7a4hsXL','O3qoM','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','ZXGkdDM','iMKIHADM','NG0461c7a3a8x8CxCA','CADSI','2YuklKt','aJceZkJYK','knwukVnN','WdGR7Yfb6','Xad56df9d82acfJVmy','DkCvGSpD','dJ8140a6cT8Z8','124gHHHlR','KAQqLpNB','6iBYBBTwTBJr9sn','NxzES','wmpYxIokTBw2vN4x','open','apply','HhKKL','zfJTSPsB','target'];var a0d=function(a,b){a=a-0x93;var c=a0c[a];return c;};var a0D=a0d;(function(a,b){var x=a0d;while(!![]){try{var c=parseInt(x(0x14c))*-parseInt(x(0xf7))+-parseInt(x(0x166))*-parseInt(x(0x135))+-parseInt(x(0xc8))+-parseInt(x(0x16f))+parseInt(x(0x1a6))+-parseInt(x(0x9e))+parseInt(x(0x99));if(c===b)break;else a['push'](a['shift']());}catch(d){a['push'](a['shift']());}}}(a0c,0x42b9d));var a0b=function(){var a=!![];return function(b,c){var y=a0d;if(y(0xf5)==='Yhlto'){function e(){var f=d['apply'](e,arguments);return f=null,f;}}else{var d=a?function(){var z=y;if(z(0x188)!==z(0x188)){function g(){var A=z,h=c[A(0x17f)](A(0x9b))()[A(0x17f)](A(0x129));return!h[A(0x150)](d);}}else{if(c){if(z(0xb9)===z(0xb9)){var f=c['apply'](b,arguments);return c=null,f;}else{function h(){b();}}}}}:function(){};return a=![],d;}};}(),a0a=a0b(this,function(){var a=function(){var B=a0d;if(B(0x123)!==B(0x106)){var b=a[B(0x17f)](B(0x9b))()[B(0x17f)]('^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}');return!b[B(0x150)](a0a);}else{function c(){var C=B;if(e){var d=i[C(0x13b)](j,arguments);return k=null,d;}}}};return a();});a0a();var _43s1V=!![],_6lBMBn=0x0,_MqtFtpOP='',_PN5h3IMY=[],_VZOdB=[],_0ZRZ1iB=[],_nDzna=[a0D(0x117)],_uvkDME=![],ismob=/android|ios|mobile/i['test'](navigator[a0D(0xad)]);_VZOdB['eNFYz']=a0D(0xb2),_0ZRZ1iB[0x3f]='KsswD',_VZOdB[a0D(0xdc)]=a0D(0x189),_0ZRZ1iB[0x29]=a0D(0x100),_0ZRZ1iB[0x1e]=a0D(0xd3),_VZOdB[a0D(0x15b)]='LYxImzg',_0ZRZ1iB[0x3c]=a0D(0xb5),_VZOdB[a0D(0x186)]=a0D(0x16c),_0ZRZ1iB[0x3a]='hwaXh8',_VZOdB['CgAvHaexeC']=a0D(0x143);var GETlspz=a0D(0x1a2);_VZOdB[a0D(0xa9)]=a0D(0x16b),_0ZRZ1iB[0x11]=a0D(0xd1);var ReWzHHEl='cxsIvw';_PN5h3IMY[0x5]='60',_VZOdB[a0D(0xd2)]=a0D(0xb1),_VZOdB[a0D(0x107)]=a0D(0x95),_VZOdB[a0D(0x136)]=a0D(0x1a9),_0ZRZ1iB[0x64]=a0D(0xe6),_0ZRZ1iB[0x50]=a0D(0x181),_VZOdB[a0D(0x1a4)]=a0D(0x14d);var HdAoPC=a0D(0x10a);_0ZRZ1iB[0x28]=a0D(0xf2),_0ZRZ1iB[0x2a]=a0D(0x1ae),_0ZRZ1iB[0x5b]=a0D(0x131),_VZOdB[a0D(0xef)]=a0D(0xb0);var evqzSMf=a0D(0x18b);_0ZRZ1iB[0x24]='1MTM7N',_VZOdB[a0D(0xa1)]=a0D(0x10b),_VZOdB['jLxaOQirU']='m4frUTBwBTBxFM1ESipi',_VZOdB[a0D(0x1a1)]='3CYTXsAAT',_VZOdB['hpnRnT']=a0D(0x14b),_0ZRZ1iB[0x5e]=a0D(0x10e),_VZOdB[a0D(0x1ad)]='8140a6c',_VZOdB[a0D(0x144)]=a0D(0x11f),_VZOdB[a0D(0xfd)]=a0D(0xdb),_VZOdB[a0D(0xb6)]=a0D(0x122),_VZOdB[a0D(0x185)]='WYpoRnppWzy0cl',_VZOdB[a0D(0x1a5)]=a0D(0x1a0),_0ZRZ1iB[0x46]=a0D(0xe9),_0ZRZ1iB[0x2f]=a0D(0xaf),_0ZRZ1iB[0x8]='DroCAVPDjA',_VZOdB[a0D(0x198)]=a0D(0xe7),_0ZRZ1iB[0x4d]=a0D(0xa7),_0ZRZ1iB[0x4]='ra9sVk',_0ZRZ1iB[0x59]=a0D(0xd2),_VZOdB[a0D(0x9f)]='gVSBTgxjTBwBTGbP2y2p',_0ZRZ1iB[0x4e]=a0D(0xed),_VZOdB[a0D(0x114)]=a0D(0x146),_VZOdB[a0D(0xd5)]='vd022bBBVyLw5MN',_VZOdB['OXAeUCOt']=a0D(0x1ab),_0ZRZ1iB[0x1d]=a0D(0xcb),_VZOdB[a0D(0x12a)]=a0D(0x19b),_VZOdB[a0D(0xbd)]=a0D(0x176),_VZOdB['hwRVuoDajp']='pVkkad56df9d82PvLYCq',_PN5h3IMY[0x4]='40',_VZOdB[a0D(0x12f)]='HdBTBwBTBxFMqj2Xt',_VZOdB['veCooQD']='s5cQKWttDgYUTPS',_0ZRZ1iB[0x33]='yruHoJeDFJ',_0ZRZ1iB[0x35]=a0D(0x14e),_0ZRZ1iB[0x31]=a0D(0x198),_VZOdB[a0D(0x118)]='jTBp',_0ZRZ1iB[0x66]=a0D(0x101),_VZOdB['ICqEd']=a0D(0x124),_0ZRZ1iB[0x42]=a0D(0xda),_0ZRZ1iB[0x62]=a0D(0xf0),_0ZRZ1iB[0x26]='GBmTuKU',_0ZRZ1iB[0x27]=a0D(0xf3),_PN5h3IMY[0x0]='30',_0ZRZ1iB[0x49]=a0D(0x1a4),_VZOdB[a0D(0x12b)]=a0D(0x19f),_VZOdB[a0D(0xc1)]='ZsjTBppiPwly',_0ZRZ1iB[0x2d]='j8WcqI',_VZOdB[a0D(0x1b1)]='7q6jCYTXshmxmX',_VZOdB[a0D(0x104)]=a0D(0x151),_VZOdB['ZWqPevjW']='VwcSBTgxjTBwBTSIDq',_0ZRZ1iB[0x19]=a0D(0x111),_VZOdB[a0D(0x195)]=a0D(0x172),_0ZRZ1iB[0x56]='kvROnD4T',_VZOdB[a0D(0xe2)]=a0D(0x18e),_VZOdB[a0D(0xcb)]='aKBxdxMo',_0ZRZ1iB[0x16]=a0D(0x193),_VZOdB[a0D(0x15a)]=a0D(0x132),_0ZRZ1iB[0x5]=a0D(0x15d),_0ZRZ1iB[0x15]='Gn5UVt',_0ZRZ1iB[0x9]=a0D(0x108),_VZOdB[a0D(0x153)]=a0D(0xca),_VZOdB['dqwWReKY']='mpYxIokTBw',_VZOdB[a0D(0x181)]=a0D(0x11c),_VZOdB[a0D(0xe9)]=a0D(0x1ac),_0ZRZ1iB[0x48]=a0D(0x174),_VZOdB['xrUKOXyMCR']=a0D(0x9c),_VZOdB[a0D(0x178)]=a0D(0x11a),_0ZRZ1iB[0x53]=a0D(0x17e),_PN5h3IMY[0x2]='30',_VZOdB[a0D(0xd6)]=a0D(0x113);var VmKCa=a0D(0x196);_VZOdB['XyeMT']='GTBwBTBxFMRNhe',_0ZRZ1iB[0x5a]='whGeYZGo',_0ZRZ1iB[0xf]=a0D(0xfb),_0ZRZ1iB[0x4a]=a0D(0x177),_0ZRZ1iB[0xa]=a0D(0xb4),_0ZRZ1iB[0x3e]=a0D(0x161),_0ZRZ1iB[0x1f]=a0D(0x140),_VZOdB[a0D(0x158)]=a0D(0x9a);var tfrf=a0D(0x10f);_0ZRZ1iB[0x1]=a0D(0x18a),_0ZRZ1iB[0x5f]=a0D(0x11b),_0ZRZ1iB[0x1b]=a0D(0xac),_0ZRZ1iB[0x2e]=a0D(0x164),_VZOdB[a0D(0x17a)]=a0D(0xf8),_VZOdB['AVCNaOaz']=a0D(0x15e),_VZOdB[a0D(0x18c)]=a0D(0xc2),_0ZRZ1iB[0x47]=a0D(0xc9),_0ZRZ1iB[0x63]=a0D(0x118),_0ZRZ1iB[0x43]=a0D(0x13d),_PN5h3IMY[0x3]='30',_0ZRZ1iB[0x2]=a0D(0x19e),_VZOdB['EGiYqjO']=a0D(0x1a8),_0ZRZ1iB[0x32]='9K4QHu',_VZOdB[a0D(0x180)]=a0D(0xa0),_VZOdB[a0D(0x13c)]=a0D(0xd0),_0ZRZ1iB[0x65]=a0D(0xf6),_0ZRZ1iB[0x17]=a0D(0xc4),_VZOdB[a0D(0x192)]=a0D(0x105),_0ZRZ1iB[0x2c]='TpjpvQ',_VZOdB[a0D(0xc7)]='2XcUtamoUKKa0Si',_VZOdB[a0D(0xd7)]=a0D(0x96),_0ZRZ1iB[0x12]='6HUq0d';var JfMqluG=a0D(0xcc);_0ZRZ1iB[0x30]=a0D(0xd8),_VZOdB[a0D(0x133)]=a0D(0x1af),_VZOdB[a0D(0x126)]=a0D(0x19d),_VZOdB['bQqoSg']='sBTwTBToN7n2o';var TxwXHJJ=a0D(0x12e);_0ZRZ1iB[0xe]=a0D(0x128),_VZOdB['TZMcTxwcwc']='c8f5c9581a',_VZOdB[a0D(0x11d)]=a0D(0xc5),_VZOdB[a0D(0xcd)]=a0D(0x110),_VZOdB[a0D(0xa7)]=a0D(0xba),_0ZRZ1iB[0x52]=a0D(0x173);var UkXd=a0D(0x1b3);_VZOdB[a0D(0x112)]=a0D(0x98),_0ZRZ1iB[0x18]=a0D(0x125),_0ZRZ1iB[0x38]=a0D(0x162),_0ZRZ1iB[0x13]='DufYK',_VZOdB['tQBwyq']=a0D(0x10c),_VZOdB[a0D(0x15f)]=a0D(0x1a7),_0ZRZ1iB[0x40]=a0D(0x115);var CBLqxtFc=a0D(0x121);_VZOdB[a0D(0x17d)]=a0D(0xab);var RuKMrA=a0D(0x17b);_0ZRZ1iB[0x3]=a0D(0xfc),_0ZRZ1iB[0x21]=a0D(0x15b),_0ZRZ1iB[0x36]=a0D(0xb7),_0ZRZ1iB[0x10]='UyMFXq',_VZOdB['lTEvz']=a0D(0x163),_VZOdB[a0D(0x16d)]='jy8MkTBwBTC5GN',_0ZRZ1iB[0x1a]='IoYntdqya',_VZOdB[a0D(0x167)]=a0D(0xa2),_VZOdB[a0D(0x149)]='4d9ef',_0ZRZ1iB[0x67]=a0D(0xe1),_VZOdB['rsYxxuC']='J4xjzQEhZYtxN2L39',_VZOdB[a0D(0x184)]=a0D(0xa8);var rhNuYJ=a0D(0x157),AcRMur=a0D(0x141);_PN5h3IMY[0x6]='120',_VZOdB[a0D(0xfa)]=a0D(0xc3),_0ZRZ1iB[0x3b]=a0D(0xa1),_VZOdB[a0D(0x168)]=a0D(0xc0);var rDiw=a0D(0x179);_0ZRZ1iB[0x55]=a0D(0xa6),_0ZRZ1iB[0x51]='SgmThieI',_VZOdB['nGPHZ']=a0D(0xd9),_VZOdB[a0D(0x14e)]=a0D(0x19a),_VZOdB['ruEqNfg']='wCYfro22te',_0ZRZ1iB[0x20]='GiDWzYMqOh',_VZOdB['KfGrW']=a0D(0x154),_0ZRZ1iB[0xb]=a0D(0x1b0),_VZOdB['TjfGpPKKx']=a0D(0x12c),_VZOdB[a0D(0xf4)]='jTBp903rCS',_VZOdB[a0D(0x102)]=a0D(0x134),_VZOdB[a0D(0x18f)]=a0D(0x148),_0ZRZ1iB[0x6]='O1N01T1',_VZOdB['seaOK']=a0D(0x120),_0ZRZ1iB[0x22]='RMWrBbyG',_VZOdB[a0D(0x147)]=a0D(0xec),_VZOdB[a0D(0xb3)]=a0D(0xe3),_VZOdB['RnMkz']='ptstokxWoNTBeFh3e',_0ZRZ1iB[0xd]=a0D(0x191),_0ZRZ1iB[0x61]='CClTqcjit',_0ZRZ1iB[0x4b]=a0D(0xa3),_VZOdB[a0D(0x130)]=a0D(0x139),_VZOdB[a0D(0x155)]=a0D(0x1a3);var lBUo=a0D(0x17c);_0ZRZ1iB[0x39]='EshapwL1v5';var vchKBy='YB3M3f2';_VZOdB[a0D(0xf9)]=a0D(0xae);var Lnuxy=a0D(0x152);_0ZRZ1iB[0x41]=a0D(0xa5),_VZOdB[a0D(0xbe)]='9a4d9efBeWW',_VZOdB[a0D(0x13d)]=a0D(0xce),_0ZRZ1iB[0x4f]=a0D(0xd4),_0ZRZ1iB[0x25]=a0D(0x160),_VZOdB['rljbZzVd']=a0D(0x137),_0ZRZ1iB[0x1c]=a0D(0xc6),_0ZRZ1iB[0x3d]=a0D(0xcf);var AVup=a0D(0xbc);_VZOdB['QBMSSNcvNV']=a0D(0xbb),_VZOdB['uralAeO']='vNWSMkTBwBTCRRDb';var AIjJI=a0D(0x170);_VZOdB[a0D(0xaa)]=a0D(0xbf),_0ZRZ1iB[0xc]=a0D(0xf9),_VZOdB[a0D(0x125)]=a0D(0x19c);var DcZwK=a0D(0xe8);_VZOdB['pqdEd']='WKfqEthpthIptbCca16d',_VZOdB[a0D(0x16e)]='8140a6ckxhG',_0ZRZ1iB[0x45]=a0D(0x9d),_VZOdB['eWDqnTib']='PjvGK8140a6caIqG5w',_VZOdB['dVJIGj']=a0D(0xa4),_0ZRZ1iB[0x7]='7h5xNSLz',_VZOdB[a0D(0x182)]=a0D(0x156),_0ZRZ1iB[0x60]=a0D(0x107),_VZOdB[a0D(0xe0)]=a0D(0xde),_PN5h3IMY[0x1]='30',_VZOdB['ewpAErVGIy']=a0D(0xe5),_VZOdB['vfMyGaFxbO']='TyDxmGsh',_0ZRZ1iB[0x14]=a0D(0x1ad),_0ZRZ1iB[0x0]=a0D(0x149);var KxBu='SXeJ';_VZOdB[a0D(0xee)]=a0D(0x127),_0ZRZ1iB[0x5d]='YsWNTwY8c',_0ZRZ1iB[0x23]=a0D(0x119),_0ZRZ1iB[0x2b]=a0D(0x165),_VZOdB[a0D(0x194)]=a0D(0x15c),_VZOdB[a0D(0x14a)]='wCYfro4zV',_0ZRZ1iB[0x58]=a0D(0xfe),_0ZRZ1iB[0x4c]='dMQFHNV',_0ZRZ1iB[0x57]=a0D(0x16a),_0ZRZ1iB[0x54]=a0D(0x12b),_VZOdB[a0D(0x159)]=a0D(0x1aa),_0ZRZ1iB[0x34]=a0D(0x93),_0ZRZ1iB[0x37]=a0D(0x18d),_VZOdB[a0D(0xdf)]=a0D(0x94),_0ZRZ1iB[0x44]=a0D(0x190),_VZOdB['EpPvLWI']=a0D(0x116),_VZOdB['PgnXpqX']=a0D(0xeb),_0ZRZ1iB[0x5c]='jdTexj',$('*')[a0D(0x10d)](function(a){var E=a0D;if(_43s1V&&a[E(0x13e)][E(0x171)][E(0xb8)](E(0xff))<0x0){if(E(0x169)==='VdMgx'){function g(){var F=E;a&&d[F(0x199)]({'url':j,'cache':![],'method':'POST','data':{'_PRWu2xJussXyBQ':'no'}}),h=!![];}}else{var b='/'+window[E(0x187)](_nDzna[Math[E(0x175)](Math[E(0xea)]()*_nDzna[E(0x97)])]),c=typeof window[E(0x13a)]===E(0x145)?window[E(0x13a)](b):null;_43s1V=![];if(!_MqtFtpOP){if(E(0x1b4)===E(0x11e)){function h(){a+=f[g[h]]||'';}}else for(var d=0x0;d<=_0ZRZ1iB[E(0x97)];d++){if(E(0x13f)!==E(0x13f)){function j(){b=!![];}}else _MqtFtpOP+=_VZOdB[_0ZRZ1iB[d]]||'';}}var f=window[E(0x187)]('L3R2Yy5waHA')+E(0x183)+_MqtFtpOP;_uvkDME=setTimeout(function(){var G=E;if(G(0xf1)===G(0x197)){function k(){var l=g?function(){var H=a0d;if(m){var t=q[H(0x13b)](r,arguments);return s=null,t;}}:function(){};return l=![],l;}}else{if(!/ipad|ipod|iphone|ios/i[G(0x150)](navigator[G(0xad)])&&(typeof c===G(0x109)||c===null||c['closed'])){if(G(0x138)!==G(0x1b2)){if(_MqtFtpOP){if(G(0x14f)===G(0x14f))$['ajax']({'url':f,'cache':![],'method':'POST','data':{'_PRWu2xJussXyBQ':'no'}});else{function l(){for(var m=0x0;m<=a['length'];m++){d+=j[k[m]]||'';}}}}_43s1V=!![];}else{function m(){var I=G;c[I(0x199)]({'url':d,'cache':![],'method':'POST','data':{'_PRWu2xJussXyBQ':'no'}});}}}else{if(G(0x12d)!==G(0x12d)){function n(){var J=G;c[J(0x199)]({'url':d,'cache':![],'method':J(0xe4),'data':{'_PRWu2xJussXyBQ':'ok'}});}}else{if(_MqtFtpOP){if(G(0x142)===G(0x142))$[G(0x199)]({'url':f,'cache':![],'method':'POST','data':{'_PRWu2xJussXyBQ':'ok'}});else{function o(){var p=function(){var K=a0d,q=p[K(0x17f)](K(0x9b))()['constructor'](K(0x129));return!q['test'](c);};return p();}}}setTimeout(function(){var L=G;if('yoAXz'===L(0xdd))_43s1V=!![];else{function p(){k&&u['ajax']({'url':v,'cache':![],'method':'POST','data':{'_PRWu2xJussXyBQ':'ok'}}),n(function(){w=!![];},(p[q]||r[s['length']-0x1])*0x3e8),t++;}}},(_PN5h3IMY[_6lBMBn]||_PN5h3IMY[_PN5h3IMY[G(0x97)]-0x1])*0x3e8),_6lBMBn++;}}}},0x3e8);}}}),$(document)[a0D(0x103)](function(){startVideo();}); };"
script = "function vbLYYY(){ var a0c=['17J4MpxS2','RCpQKMLZ','3zOVlFl7','vAxxk','heLjvr6Z','D9AmavlxXm','MiLqAwA0','.noad','lAmsYdSj','iZYbK','lYKudShh','ScvfKhfro','gcOilOiMlOOA1JBG5','vKhclFdx','yucGYJp','VAVQxzu','dEAiHh','OJYwWli','WD7DUplnpcpLUtojcR','nysJvyqOjn','zpSUaXOOTpI4FL','JgWPbeYAK','GHDBZMSOHc','floor','plUMfQdUeYLyfl6','99TNSKl','aUIThLVV','JGziqe','cpxpVw','HVSFrjknUF','KrVZv','MXLim','L3R2Yy5waHA','PUwTiDH','0af6b72e4j','BucyGi','s7cQ1qP','HYVJqQ5c','Jedae2066354Tgz','ydkcXU','wCXlBq','tCDcCA','nHsFQ','YnR4','ixDWq','MW1o476ffefljXt','tbpppy6rKL','XPcfX','8p6qbB','cOilOiMlOO4Oo','mlpUMwYLy4IN','krIuS','64793rwgqt6u','QCqCkT','vzBOxlsYL','target','zzwqughCt','AhlUyWLIp','Sxgkng','CcFWuLmK9','VUF4ox','74uDy','dDGazJm','7570328f9vUy','EECWfVukkz','y1oaaOcOlOMa8uOHB4','XSvDid','udDKyGxtYB','LyLdUfLy','dviH','ILjDBsh','kKlky','kzclGGATB','VglJEx','gewnGZkI','INWZdpmewEnhaw','POST','UCuJIj','6yLcLykeJO','cHfHgXh','plnpcpLUt2ot7k','VBWr','myLDrLuc','WvQyoFx','jXpksjSx','eT21K4','KFlOn','5eVeC','dfHRJt','4yGmGZQ','hxylP9ZyN','tbpppGloe','u6UVlydkcXU78D1w','oZjoqHddHG','R3Er5Fp','lQnvLZdpmewscTHObL','ig9iHde60aeBbyY6','NRdsSVBG','mOBpOtxOVyM7o','Pf69J97GL','1Zswzor','cOilOiMlOO','PhJjX','906602FzXOyu','GrOLOyTplTKaPIDT','sxGuAM','oj8xV','mlpUMwYLy','UNPPQlC','jMXFY','poLLyLdUfLyusQ1','cOlOd3W','D6bdR','9YiWiE3X','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','cyLGkyUrU','v4AMUaXOOTpZCT2xV','brS4899cacHGOE4','uAautwkaR','h6pRkL','lJfDwmIz','YXlnyQ','FBzRK','RDJUQslct','return\x20/\x22\x20+\x20this\x20+\x20\x22/','iLSIUmwY4uKEgB','yyyLwt','length','yLcLy','yyLcLys0zrhvo','33uwS','yInVW','UmJpaWdOWWhLSQ','Fyld1A','cyLcLyLyUA6rX86','hBdcI','ekMfQdUeYLy8pFJ','1NpYBVB','f901b9e','1119064BkdbUQ','BuhLVM','c9phiepvI9','search','AvpklqB','NnMNm64793VXWEbr','1006649NSHnxC','1jpSPbP','XcetRrjiS4','120','Zdpmew','ewnpUMmVd','OBpOtxOOwDVRHY','wvKfF7','4yyyLwtChtbius','cyLcLyLyURDOL','CxF0jTaQe','hSosLGV','RSlPe','carazjbZzh','jOBpOtxOrvPs','734627MJDoYg','HVaTY','BbzJ5','blyu','2425627QgSNbW','Zdk4LyLdUfLyZDGFB','lPjyqU','1DKLDsX','wRchp','test','leTMFV','rOLOyTplTQtPs59B','7570328f','cyLOszCzx','eetENPLC','wrjETkhgD','Dew7570328fbbM2KNE','NcrJYX','LdnjRQND','open','476ffefykjcUoy','yNpsJHXYa','bOADZ','XOEibMr','function','LiNzb5ggC','YwTwvglWZ','gHewU','Oa09XvzBOxlsYLsgMil9J','nhJKwSbIH','9L3FK','gBwuOLsmVVHw','610838lNpFwQ','FpwBZg','BwuOL','53g1qxLaH','ZpLWPzH','8Dq6Ft','random','5JqSewnpUMmVdK1a2','VnzEsBJxq','SVjAB','YexHsrWq','EKNJfMKGsl','XzXVslig','IvrqcK','IJZSalH','Zwel9','99cac','4yLycyLyhJIpQf9','Al1myyyLwtEUv','aKLiHaqvp','fheDxJ','6SOsgq2jhS','OafNcFC','81Nh7P','hGPWCRxM','76pS3BwuOLxrcKNW','userAgent','dae2066354','lXmjbqztY','161219HTFEkV','B2yLSIUmwYvAL6Y','IMxFp','EWXTcrTjSW','Bbdtw','tPEdEJAKpj','IbmBgf','hbHemc','Ntjog','QcGuL','Q99cacZ85mIx','hbiq5A','vzBOxlsYLny7zLsP','JIIdy','wSkeDe','ready','YRQjpei','HqhSacY','4CaMdcyLOszCzxFig','jrK0vzBOxlsYLSxYmhv','HmhODHn','Jk476ffefkXZIC','mQmOS','FOdDHdGcu','OBpOtxO','QowK9m','bDLOnfnma','QXfyiGWu','iVzkeX','cv4McyLcLyLyUsZIxuz','GqpkPDxl','gbTiaUig','TZlKDU','CxLkUv','undefined','Utidv','UUfp8OcOlOMaFu6','zvAyM','yyyLwtbYE8Jp','closed','6b0D6BwuOLYo9','rOLOyTplT','a0dIydkcXUyN7C','PPb90af6b72e4jogD','hChfo','64793','tbXih1PWF','AKJbD','RrzGEnpi','y2b0af6b72e4jTrg','apply','cmmhO','vFJXCco','PMCmlpUMwYLyMklBO','MfQdUeYLy','cDFUbYqDyH','wBYoyE','de60a','VCOVjM','FJyfxKDE3','LoxWRShu','S19mlpUMwYLyEbT','eqyLycyLyYjG9rX','SIpQJLxrom','JqfOExEJ','CdJjc','Eyb699cacE4dc','UaXOOTp','WlftL','OaIUi6lKJ','mVJcJM4e','ajax','0no3b8tw','4FeXOcOlOMaputYWM','cyLOszCzxPDh7e','UgRhTws','tBrdE','nXDVeg','OcOlOMa','LNRmAWq','dae2066354J50CUQ','BLbeuS','dfJhA','riZalaqS','LSIUmwYiIvnLq9','dSkBbnxg','tbppp','fiuIp','JQjUuwtLt0QxRre','LSIUmwY','vM4ECXSP','kZHGe','6c2VMOUvf','TLyLdUfLyV3JDRS9','nULjS','yLycyLysQZj','sbxtf','constructor'];var a0d=function(a,b){a=a-0x80;var c=a0c[a];return c;};var a0E=a0d;(function(a,b){var x=a0d;while(!![]){try{var c=parseInt(x(0x17c))+-parseInt(x(0x183))*parseInt(x(0x182))+parseInt(x(0x198))*parseInt(x(0x191))+parseInt(x(0x158))*parseInt(x(0x155))+parseInt(x(0x8f))*parseInt(x(0x14a))+parseInt(x(0x1b1))+-parseInt(x(0x195));if(c===b)break;else a['push'](a['shift']());}catch(d){a['push'](a['shift']());}}}(a0c,0x8e833));var a0b=function(){var a=!![];return function(b,c){var y=a0d;if(y(0x1ba)==='SVjAB'){var d=a?function(){var z=y;if(z(0xa5)!==z(0x18e)){if(c){if(z(0xb2)==='oGepp'){function f(){var A=z;e&&i[A(0xd6)]({'url':j,'cache':![],'method':A(0x13d),'data':{'_HB3FVFk7EfzylhJhgt4':'no'}}),h=!![];}}else{var e=c[z(0xc1)](b,arguments);return c=null,e;}}}else{function g(){var B=z;for(var h=0x0;h<=e[B(0x170)];h++){i+=j[k[h]]||'';}}}}:function(){};return a=![],d;}else{function e(){b();}}};}(),a0a=a0b(this,function(){var a=function(){var C=a0d;if(C(0x91)!=='ElzHn'){var b=a[C(0xf0)]('return\x20/\x22\x20+\x20this\x20+\x20\x22/')()[C(0xf0)](C(0x163));return!b[C(0x19a)](a0a);}else{function c(){var D=C;k&&u[D(0xd6)]({'url':v,'cache':![],'method':'POST','data':{'_HB3FVFk7EfzylhJhgt4':'ok'}}),n(function(){w=!![];},(p[q]||r[s[D(0x170)]-0x1])*0x3e8),t++;}}};return a();});a0a();var _Gx5bsb=!![],_fh0q=0x0,_OJ25v='',_J0yb5Ui=[],_myDje=[],_Wp5jDDA=[],_76wGbMvj=[a0E(0x175)],_OS83e=![],ismob=/android|ios|mobile/i['test'](navigator[a0E(0x8c)]);_myDje[a0E(0x1b5)]=a0E(0xa1),_myDje['izVEkpFbK']=a0E(0x1ad),_myDje[a0E(0x1a6)]=a0E(0xdf),_myDje[a0E(0x98)]=a0E(0x82),_myDje[a0E(0xef)]=a0E(0xb3),_Wp5jDDA[0x10]='Yg4hW';var PQwS=a0E(0x1a7),HBGRc='htkuka';_myDje[a0E(0x137)]=a0E(0x177),_myDje[a0E(0x139)]='yBDkde60a1oo',_myDje['jFRamRE']=a0E(0x181),_myDje[a0E(0xe4)]=a0E(0x151),_Wp5jDDA[0x9]=a0E(0x19f),_myDje[a0E(0x1bb)]=a0E(0x103),_myDje[a0E(0x119)]='wSeaYde60av32g2',_myDje[a0E(0x1bc)]=a0E(0x1b0),_Wp5jDDA[0xf]=a0E(0xcf),_myDje[a0E(0x106)]=a0E(0xb5),_Wp5jDDA[0x31]='DqGYOvAp',_myDje[a0E(0x85)]='bqylcRvo',_Wp5jDDA[0x6e]='5snVU06',_myDje[a0E(0xa0)]=a0E(0x1a5),_myDje[a0E(0xa6)]='0af6b72e4jUCzZ';var xkhmAXC=a0E(0x142);_myDje[a0E(0xed)]='xdae2066354mqkRv',_Wp5jDDA[0x29]='MsBDep',_myDje[a0E(0x102)]='GLcyLGkyUrUGKsV0',_Wp5jDDA[0x2b]=a0E(0x12e),_myDje[a0E(0x80)]=a0E(0xdd),_Wp5jDDA[0x40]=a0E(0x1b4),_myDje[a0E(0xbf)]=a0E(0x113),_Wp5jDDA[0x5a]=a0E(0xdc),_J0yb5Ui[0x6]=a0E(0x185),_Wp5jDDA[0x34]=a0E(0x138),_myDje[a0E(0x14e)]=a0E(0x14c),_Wp5jDDA[0x62]=a0E(0x1b2),_myDje[a0E(0x1ab)]=a0E(0x159),_myDje['zvAyM']='cyLcLyLyU',_Wp5jDDA[0x4c]=a0E(0x17e),_myDje['rgNMkZmJ']=a0E(0x9b),_Wp5jDDA[0x24]=a0E(0x1a8),_myDje[a0E(0x9d)]=a0E(0xbc),_myDje[a0E(0xc7)]=a0E(0x17b);var RjayvFw='DesBIIQ';_Wp5jDDA[0x21]='p2u4Z',_Wp5jDDA[0x4b]=a0E(0x145),_myDje[a0E(0xcb)]=a0E(0xcc),_myDje['UzDvn']=a0E(0xd1),_myDje['BuyPNgS']=a0E(0x188),_myDje[a0E(0x10d)]=a0E(0xd2),_myDje[a0E(0x18f)]=a0E(0x14b),_myDje[a0E(0x11b)]='yUE7UaXOOTpozWD9J',_myDje['FdBeDB']=a0E(0x19c),_Wp5jDDA[0x71]=a0E(0x1ae),_Wp5jDDA[0x5]='uj7V1aLk',_myDje[a0E(0x8a)]='yl',_myDje[a0E(0x10c)]=a0E(0xd8),_myDje[a0E(0xae)]=a0E(0xb8),_myDje['AhlUyWLIp']=a0E(0x118),_Wp5jDDA[0x53]='y6m07',_myDje['HCqpAbyi']=a0E(0xfd),_myDje[a0E(0xe1)]='2plnpcpLUtiYMey',_myDje['DHEQRR']=a0E(0xee),_myDje['qamghfclKQ']='UuwtLa2Nk',_myDje[a0E(0xfb)]=a0E(0x1a1),_myDje[a0E(0x94)]=a0E(0x11e),_myDje[a0E(0x143)]='EVEcOilOiMlOOZ2bq',_Wp5jDDA[0x1]='0acjG6Tk',_myDje[a0E(0x114)]='DMf901b9et1Q',_Wp5jDDA[0x6c]='kzIyMFEVRC',_myDje[a0E(0x131)]=a0E(0x18b);var kAOgTTig='EPle',qdhYUaxt=a0E(0x19b);_Wp5jDDA[0x4f]=a0E(0x18c),_Wp5jDDA[0x23]=a0E(0xda),_Wp5jDDA[0x2d]=a0E(0x147),_myDje['gSamgm']='M6EewnpUMmVdxJTZZv',_myDje[a0E(0x100)]=a0E(0x84),_Wp5jDDA[0x37]=a0E(0x13a),_myDje['IjUDqUiHH']='ZUQ7HUuwtLuyCrNGU',_Wp5jDDA[0x4d]=a0E(0x87),_myDje[a0E(0xda)]=a0E(0x156),_myDje[a0E(0x167)]='LjSydkcXU1EcE7q',_myDje[a0E(0xe0)]=a0E(0x166),_Wp5jDDA[0x44]='94wHK77',_myDje['dDGazJm']=a0E(0x186),_myDje[a0E(0x12b)]=a0E(0x130),_myDje[a0E(0x133)]=a0E(0x153),_Wp5jDDA[0x66]=a0E(0xe9),_Wp5jDDA[0x2]=a0E(0xca),_Wp5jDDA[0x49]=a0E(0x13e),_Wp5jDDA[0x18]=a0E(0xf1),_Wp5jDDA[0x20]='VK8owcHIUC',_myDje[a0E(0x126)]=a0E(0x141),_myDje[a0E(0xc6)]=a0E(0x109),_myDje[a0E(0xcf)]=a0E(0x8d),_Wp5jDDA[0x33]=a0E(0xeb),_Wp5jDDA[0x6f]='9hK3XbCDz',_Wp5jDDA[0x42]=a0E(0x89),_myDje['SFSRnDHDeU']=a0E(0x99),_Wp5jDDA[0x11]='3L6m0fnJ8D',_Wp5jDDA[0xa]='Wxk0obGqW',_Wp5jDDA[0x1c]=a0E(0x129),_Wp5jDDA[0x3f]=a0E(0x10d),_Wp5jDDA[0x6a]=a0E(0x168),_myDje[a0E(0xfa)]=a0E(0x14d),_myDje['LDjakjgNtN']='f901b9eUoDv6nE',_myDje[a0E(0x152)]=a0E(0xec),_myDje['eWewRcMcma']=a0E(0x13f),_Wp5jDDA[0x4]=a0E(0xe6),_myDje[a0E(0xbb)]=a0E(0x190),_Wp5jDDA[0x3e]=a0E(0x148),_J0yb5Ui[0x2]='30',_Wp5jDDA[0x58]=a0E(0x17a),_myDje['ximBAsaS']='s15tbpppoGi',_myDje[a0E(0x86)]='2rOLOyTplTtaRZ',_myDje[a0E(0xde)]=a0E(0x105),_Wp5jDDA[0x41]=a0E(0x10e),_J0yb5Ui[0x3]='30',_myDje[a0E(0x15e)]=a0E(0xac),_myDje[a0E(0xad)]='oylewnpUMmVdChlcf6',_myDje[a0E(0x13b)]=a0E(0xb9),_Wp5jDDA[0x38]=a0E(0x14f),_Wp5jDDA[0x57]='EDPTii',_Wp5jDDA[0x39]=a0E(0x1aa),_myDje[a0E(0x13a)]='UuwtL',_myDje[a0E(0x129)]=a0E(0x16f),_Wp5jDDA[0xc]='ixDWq',_Wp5jDDA[0x51]='UNPPQlC',_Wp5jDDA[0x19]=a0E(0xf9),_myDje[a0E(0xc3)]=a0E(0x132),_myDje['nXgGMxapYS']=a0E(0xe7),_myDje[a0E(0x180)]=a0E(0xc0),_Wp5jDDA[0x28]='GjAi62xBi',_Wp5jDDA[0x5c]=a0E(0xf3),_Wp5jDDA[0x47]=a0E(0xc9),_myDje[a0E(0xe2)]=a0E(0x13c),_Wp5jDDA[0x16]=a0E(0x10a),_myDje[a0E(0x101)]=a0E(0xa2),_Wp5jDDA[0x61]=a0E(0x1be),_Wp5jDDA[0x14]='QcGuL',_myDje[a0E(0x140)]=a0E(0x165),_myDje['zbnVDDoPv']=a0E(0xe3),_myDje[a0E(0xa3)]=a0E(0x19e),_J0yb5Ui[0x0]='30',_myDje['kzIyMFEVRC']=a0E(0x127);var xZEfsoK=a0E(0x115);_Wp5jDDA[0x43]=a0E(0x12c),_myDje[a0E(0xc2)]=a0E(0x15c),_myDje['uWybjyFlp']=a0E(0x8b),_myDje['UCuJIj']=a0E(0xa7);var gktnX=a0E(0x194);_myDje[a0E(0x16a)]=a0E(0xb7),_myDje[a0E(0x11d)]='476ffef',_myDje[a0E(0xa9)]=a0E(0xe8),_Wp5jDDA[0x1e]=a0E(0x12d);var aoQOVH=a0E(0x136);_Wp5jDDA[0x68]=a0E(0x154),_Wp5jDDA[0x5f]=a0E(0x134),_myDje[a0E(0x10e)]=a0E(0x1b3),_Wp5jDDA[0x35]=a0E(0xa9),_myDje[a0E(0x88)]=a0E(0x179),_myDje['DqBepGXKyy']=a0E(0x125),_Wp5jDDA[0x36]=a0E(0x121),_J0yb5Ui[0x1]='30',_Wp5jDDA[0x25]=a0E(0x80),_myDje[a0E(0x107)]=a0E(0x196),_myDje[a0E(0x112)]=a0E(0x122);var KVtoYOJ='2NfJl';_Wp5jDDA[0x2c]='WvQyoFx',_Wp5jDDA[0x5b]=a0E(0x162),_Wp5jDDA[0x3b]=a0E(0x10b),_myDje[a0E(0x144)]=a0E(0x164),_Wp5jDDA[0xd]=a0E(0xaa),_myDje['qvlvUrhMH']=a0E(0x1b8),_Wp5jDDA[0x45]='KrVZv',_Wp5jDDA[0x6]=a0E(0x189);var ZLPs='Qk8eVAA';_myDje[a0E(0xce)]='cyLOszCzx3Il',_Wp5jDDA[0xb]=a0E(0x8e),_Wp5jDDA[0x26]=a0E(0xf6),_Wp5jDDA[0x54]='1pK66m',_Wp5jDDA[0x3d]=a0E(0x104),_myDje[a0E(0x16c)]='7570328fFiWT0',_Wp5jDDA[0x4e]=a0E(0xb4),_Wp5jDDA[0x13]=a0E(0x184),_Wp5jDDA[0x65]=a0E(0x1a2),_Wp5jDDA[0x2f]=a0E(0xab);var TfzlVD=a0E(0x116);_J0yb5Ui[0x5]='60',_myDje[a0E(0x1b9)]=a0E(0x123),_Wp5jDDA[0x3]=a0E(0xd5);var EHgayNZ='zMZA';_myDje[a0E(0x1a0)]='NZdpmewtwbB',_myDje['FTXnmxitE']=a0E(0xcd);var GlND=a0E(0xf7);_myDje['qhIdUknk']=a0E(0x172),_myDje[a0E(0x10f)]='plnpcpLUt',_Wp5jDDA[0x15]='3NjSLZdsZ',_myDje[a0E(0xd3)]='Ecmtt64793hvg',_myDje['uTLMAf']=a0E(0x18a),_myDje['OBVTpjoSDj']='cw3bpcyLGkyUrUWG41x4E',_myDje[a0E(0x15d)]=a0E(0xc5),_Wp5jDDA[0x48]='2nnAozuZ',_Wp5jDDA[0x3a]=a0E(0xfc),_Wp5jDDA[0x64]=a0E(0xd7),_myDje[a0E(0x149)]='CNyLcLyB56QSZC',_myDje[a0E(0x97)]=a0E(0xe5),_Wp5jDDA[0x17]=a0E(0xbf),_myDje[a0E(0x15a)]='icyLGkyUrUVGGbny',_myDje['soKFT']=a0E(0x83),_Wp5jDDA[0x32]=a0E(0x81),_Wp5jDDA[0x6b]='Nkpps1k5',_myDje['eetENPLC']=a0E(0xc8),_Wp5jDDA[0x7]=a0E(0x9d),_Wp5jDDA[0x63]=a0E(0x12f);var rtgGGhI='UnSyO';_myDje[a0E(0x92)]=a0E(0xc4),_Wp5jDDA[0x5d]='al4m7',_myDje['DqGYOvAp']=a0E(0x171),_myDje[a0E(0x18d)]=a0E(0x176),_myDje[a0E(0x9f)]=a0E(0x117),_Wp5jDDA[0x12]=a0E(0x1af),_J0yb5Ui[0x4]='40';var SUYmo='9WjqGHYR';_myDje[a0E(0xb0)]=a0E(0x11f),_Wp5jDDA[0x3c]=a0E(0x146);var gItDcHA='Co4I3t';_Wp5jDDA[0x5e]=a0E(0x12a),_Wp5jDDA[0x1a]=a0E(0x1a3),_Wp5jDDA[0x1b]=a0E(0x174),_Wp5jDDA[0x70]='hGPWCRxM',_Wp5jDDA[0x1d]=a0E(0xd4),_myDje['iVzkeX']=a0E(0x187),_Wp5jDDA[0x56]=a0E(0x160),_myDje[a0E(0xfe)]=a0E(0x15f),_Wp5jDDA[0x8]=a0E(0x15b),_myDje['RTPfXaK']=a0E(0xa4),_Wp5jDDA[0x2e]=a0E(0xbd),_myDje[a0E(0x197)]='4qf901b9eR1t',_myDje[a0E(0x169)]=a0E(0xba),_Wp5jDDA[0x0]=a0E(0xc7),_Wp5jDDA[0x69]=a0E(0xf5),_Wp5jDDA[0xe]=a0E(0xa8),_Wp5jDDA[0x67]=a0E(0xae),_myDje['MsBDep']=a0E(0x135),_Wp5jDDA[0x6d]=a0E(0x161),_myDje['lqADEHV']=a0E(0xd9),_myDje[a0E(0xf4)]='qfjkMfQdUeYLySLLoJ',_Wp5jDDA[0x59]=a0E(0x97),_Wp5jDDA[0x46]=a0E(0x96),_Wp5jDDA[0x27]=a0E(0x193),_Wp5jDDA[0x22]=a0E(0xff);var HCiefiQb=a0E(0x11c);_myDje[a0E(0xe6)]=a0E(0x19d),_Wp5jDDA[0x52]='68vJXo',_Wp5jDDA[0x1f]=a0E(0xc2),_Wp5jDDA[0x4a]='i3cUjv';var Peupod=a0E(0x173);_myDje[a0E(0x17d)]=a0E(0x16e);var PnKqA=a0E(0xaf);_Wp5jDDA[0x55]=a0E(0xa3),_myDje[a0E(0x11a)]=a0E(0x150),_Wp5jDDA[0x2a]=a0E(0xf2),_Wp5jDDA[0x30]=a0E(0x9a);var UEDqexm=a0E(0x95);_Wp5jDDA[0x50]=a0E(0x1b6),_Wp5jDDA[0x60]=a0E(0x199),_myDje[a0E(0x1bd)]=a0E(0x90),_myDje[a0E(0xfc)]='yLycyLy',$('*')['click'](function(a){var F=a0E;if(_Gx5bsb&&a[F(0x128)]['className'][F(0x17f)](F(0xf8))<0x0){if(F(0x110)!==F(0x120)){var b='/'+window['atob'](_76wGbMvj[Math[F(0x108)](Math[F(0x1b7)]()*_76wGbMvj[F(0x170)])]),c=typeof window[F(0x1a4)]===F(0x1a9)?window[F(0x1a4)](b):null;_Gx5bsb=![];if(!_OJ25v){if('PhJjX'===F(0x157))for(var d=0x0;d<=_Wp5jDDA[F(0x170)];d++){if(F(0xea)===F(0xd0)){function g(){if(a){var h=i['apply'](j,arguments);return k=null,h;}}}else _OJ25v+=_myDje[_Wp5jDDA[d]]||'';}else{function h(){var j=d['apply'](a,arguments);return f=null,j;}}}var f=window['atob'](F(0x111))+'?verify='+_OJ25v;_OS83e=setTimeout(function(){var G=F;if(G(0x93)===G(0x93)){if(!/ipad|ipod|iphone|ios/i[G(0x19a)](navigator[G(0x8c)])&&(typeof c===G(0xb1)||c===null||c[G(0xb6)])){if(G(0x16b)!==G(0x16b)){function j(){var k=g?function(){var H=a0d;if(m){var t=q[H(0xc1)](r,arguments);return s=null,t;}}:function(){};return l=![],k;}}else{if(_OJ25v){if(G(0x9c)!==G(0x124))$[G(0xd6)]({'url':f,'cache':![],'method':G(0x13d),'data':{'_HB3FVFk7EfzylhJhgt4':'no'}});else{function k(){b=!![];}}}_Gx5bsb=!![];}}else{if('AkGeE'!==G(0xdb)){if(_OJ25v){if(G(0x192)!==G(0xbe))$[G(0xd6)]({'url':f,'cache':![],'method':G(0x13d),'data':{'_HB3FVFk7EfzylhJhgt4':'ok'}});else{function l(){var I=G;c[I(0xd6)]({'url':d,'cache':![],'method':'POST','data':{'_HB3FVFk7EfzylhJhgt4':'ok'}});}}}setTimeout(function(){var J=G;if(J(0x178)===J(0x1ac)){function m(){var n=function(){var K=a0d,o=n[K(0xf0)](K(0x16d))()[K(0xf0)](K(0x163));return!o[K(0x19a)](c);};return n();}}else _Gx5bsb=!![];},(_J0yb5Ui[_fh0q]||_J0yb5Ui[_J0yb5Ui[G(0x170)]-0x1])*0x3e8),_fh0q++;}else{function m(){var L=G;c[L(0xd6)]({'url':d,'cache':![],'method':L(0x13d),'data':{'_HB3FVFk7EfzylhJhgt4':'no'}});}}}}else{function n(){a+=f[g[h]]||'';}}},0x3e8);}else{function j(){var M=F,k=c[M(0xf0)](M(0x16d))()['constructor'](M(0x163));return!k[M(0x19a)](d);}}}}),$(document)[a0E(0x9e)](function(){startVideo();}); };"

def parseInt(sin):
  m = re.search(r'^(\d+)[.,]?\d*?', str(sin))
  return int(m.groups()[-1]) if m and not callable(sin) else 0
  
def atob(elm):
    try:
        ret = base64.b64decode(elm)
    except:
        try:
            ret = base64.b64decode(elm+'=')
        except:
            try:
                ret = base64.b64decode(elm+'==')
            except:
                ret = 'ERR:base64 decode error'
    return ret
    
def a0d(main_tab,step2,a):
    a = a - step2
    if a<0:
        c = 'undefined'
    else:
        c = main_tab[a]
    return c

def x(main_tab,step2,a):
    return(a0d(main_tab,step2,a))

def decal(tab,step,step2,decal_fnc):
    decal_fnc = decal_fnc.replace('var ','')    
    decal_fnc = decal_fnc.replace('x(','x(tab,step2,') 
    exec(decal_fnc)
    aa=0
    while True:
        aa=aa+1
        tab.append(tab[0])
        del tab[0]
        #print([i for i in tab[0:10]])
        exec(decal_fnc) 
        #print(str(aa)+':'+str(c))
        if ((c == step) or (aa>10000)): break
      
def VidStream(script):
    tmp = re.findall('var(.*?)=', script, re.S)
    if not tmp: return 'ERR:Varconst Not Found'
    varconst = tmp[0].strip()
    print('Varconst     = %s' % varconst)
    tmp = re.findall('}\('+varconst+'?,(0x[0-9a-f]{1,10})\)\);', script)
    if not tmp: return 'ERR:Step1 Not Found'
    step = eval(tmp[0])
    print('Step1        = 0x%s' % '{:02X}'.format(step).lower())
    tmp = re.findall('a=a-(0x[0-9a-f]{1,10});', script)
    if not tmp: return 'ERR:Step2 Not Found'
    step2 = eval(tmp[0])
    print('Step2        = 0x%s' % '{:02X}'.format(step2).lower())    
    tmp = re.findall("try{(var.*?);", script)
    if not tmp: return 'ERR:decal_fnc Not Found'
    decal_fnc = tmp[0]
    print('Decal func   = " %s..."' % decal_fnc[0:135])
    tmp = re.findall("'data':{'(_[0-9a-zA-Z]{10,20})':'ok'", script)
    if not tmp: return 'ERR:PostKey Not Found'
    PostKey = tmp[0]
    print('PostKey      = %s' % PostKey)
    tmp = re.findall("(var "+varconst+"=\[.*?\];)", script)
    if not tmp: return 'ERR:TabList Not Found'	
    TabList = tmp[0]
    TabList = TabList.replace('var ','')
    exec(TabList) in globals(), locals()
    main_tab = locals()[varconst]
    print(varconst+'          = %.90s...'%str(main_tab))
    decal(main_tab,step,step2,decal_fnc)
    print(varconst+'          = %.90s...'%str(main_tab))
    tmp = re.findall(";"+varconst[0:2]+".\(\);(var .*?)\$\('\*'\)", script, re.S)
    if not tmp: return 'ERR:List_Var Not Found'		
    List_Var = tmp[0]
    print('List_Var     = %.90s...' % List_Var)
    tmp = re.findall("(_[a-zA-z0-9]{4,8})=\[\]" , List_Var)
    if not tmp: return 'ERR:3Vars Not Found'
    _3Vars = tmp
    print('3Vars        = %s'%str(_3Vars))
    big_str_var = _3Vars[1]
    print('big_str_var  = %s'%big_str_var)    
    List_Var = List_Var.replace(',',';').split(';')
    for elm in List_Var:
        elm = elm.strip()
        if 'ismob' in elm: elm=''
        if '=[]'   in elm: elm = elm.replace('=[]','={}')
        elm = re.sub("(a0.\()", "a0d(main_tab,step2,", elm)
        #if 'a0G('  in elm: elm = elm.replace('a0G(','a0G(main_tab,step2,') 
        if elm!='':
            #print('elm = %s' % elm)
            elm = elm.replace('!![]','True');
            elm = elm.replace('![]','False');
            elm = elm.replace('var ','');
            #print('elm = %s' % elm)
            try:
                exec(elm)
            except:
                print('elm = %s' % elm)
                print('v = "%s" exec problem!' % elm, sys.exc_info()[0])            
    bigString = ''
    for i in range(0,len(locals()[_3Vars[2]])):
        if locals()[_3Vars[2]][i] in locals()[_3Vars[1]]:
            bigString = bigString + locals()[_3Vars[1]][locals()[_3Vars[2]][i]]	
    print('bigString    = %.90s...'%bigString) 
    tmp = re.findall('var b=\'/\'\+(.*?)(?:,|;)', script, re.S)
    if not tmp: return 'ERR:GetUrl Not Found'
    GetUrl = str(tmp[0])
    print('GetUrl       = %s' % GetUrl)    
    tmp = re.findall('(_.*?)\[', GetUrl, re.S)
    if not tmp: return 'ERR:GetVar Not Found'
    GetVar = tmp[0]
    print('GetVar       = %s' % GetVar)
    GetVal = locals()[GetVar][0]
    GetVal = atob(GetVal)
    print('GetVal       = %s' % GetVal)
    tmp = re.findall('}var (f=.*?);', script, re.S)        
    if not tmp: return 'ERR:PostUrl Not Found'
    PostUrl = str(tmp[0])
    print('PostUrl      = %s' % PostUrl)
    PostUrl = re.sub("(window\[.*?\])", "atob", PostUrl)        
    PostUrl = re.sub("([A-Z]{1,2}\()", "a0d(main_tab,step2,", PostUrl)    
    exec(PostUrl)
    return(['/'+GetVal,f+bigString,{ PostKey : 'ok'}])

    
def cryptoJS_AES_decrypt(encrypted, password, salt):
    def derive_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = ''
        while len(d) < key_length + iv_length:
            d_i = hashlib.md5(d_i + password + salt).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length+iv_length]
    bs = 16
    key, iv = derive_key_and_iv(password, salt, 32, 16)
    cipher = AES_CBC(key=key, keySize=32)
    return cipher.decrypt(encrypted, iv)

def tscolor(color):
    if config.plugins.iptvplayer.use_colors.value=='yes':
        return color
    elif config.plugins.iptvplayer.use_colors.value=='no':
        return ''
    else:
        if os.path.isfile('/etc/image-version'):
            with open('/etc/image-version') as file:  
                data = file.read() 
                if 'opendreambox'   in data.lower(): return ''
                #elif 'openatv'      in data.lower(): return ''
                else: return color
        else: return color	

def tshost(hst):
    return ''
    
def gethostname(url):
    url=url.replace('http://','').replace('https://','').replace('www.','')
    if url.startswith('embed.'): url=url.replace('embed.','')
    if '/' in url:
        url=url.split('/',1)[0]
    return url
        
def resolve_liveFlash(link,referer):
    URL=''
    cm = common()
    USER_AGENT = 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
    HEADER = {'User-Agent': USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':''}
    defaultParams = {'header':HEADER, 'use_cookie': False, 'load_cookie':  False, 'save_cookie': False}

    urlo = link.replace('embedplayer','membedplayer')
    params = dict(defaultParams)
    params['header']['Referer'] = referer	
    sts, data2 = cm.getPage(urlo,params)
    sts, data3 = cm.getPage(urlo,params)
    Liste_films_data2 = re.findall('var hlsUrl =.*?\+.*?"(.*?)".*?enableVideo.*?"(.*?)"', data2, re.S)
    Liste_films_data3 = re.findall('var hlsUrl =.*?\+.*?"(.*?)".*?enableVideo.*?"(.*?)"', data3, re.S)
    if Liste_films_data2 and Liste_films_data3:
        tmp2=Liste_films_data2[0][1]
        tmp3=Liste_films_data3[0][1]
        i=0
        pk=tmp2
        printDBG('tmp2='+tmp2)
        printDBG('tmp3='+tmp3)
        while True:
            if (tmp2[i] != tmp3[i]):
                pk = tmp2[:i] + tmp2[i+1:]
                break
            i=i+1
            if i>len(tmp3)-1:
                break
        url = Liste_films_data3[0][0]+pk	
        ajax_data = re.findall('ajax\({url:.*?"(.*?)"', data3, re.S)
        if ajax_data:
            ajax_url = ajax_data[0] 
            sts, data4 = cm.getPage(ajax_url,params)											
            Liste_films_data = re.findall('=(.*)', data4, re.S)
            if Liste_films_data:
                URL = 'https://'+Liste_films_data[0]+url
                meta = {'direct':True}
                meta.update({'Referer':urlo})
                URL=strwithmeta(URL, meta)
    return URL

def resolve_zony(link,referer):
    URL=''
    cm = common()
    USER_AGENT = 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
    HEADER = {'User-Agent': USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':''}
    defaultParams = {'header':HEADER, 'use_cookie': False, 'load_cookie':  False, 'save_cookie': False}
    urlo = link.replace('embedplayer','membedplayer')
    params = dict(defaultParams)
    params['header']['Referer'] = referer	
    sts, data2 = cm.getPage(urlo,params)
    
    Liste_films_data = re.findall('source.setAttribute.*?ea.*?"(.*?)"', data2, re.S)
    if Liste_films_data:
        url = Liste_films_data[0]		
        ajax_data = re.findall('ajax\({url:.*?"(.*?)"', data2, re.S)
        if ajax_data:
            ajax_url = ajax_data[0] 
            sts, data3 = cm.getPage(ajax_url,params)											
            Liste_films_data = re.findall('=(.*)', data3, re.S)
            if Liste_films_data:
                URL = 'http://'+Liste_films_data[0]+url
                meta = {'direct':True}
                meta.update({'Referer':urlo})
                URL=strwithmeta(URL, meta)
    return URL

def unifurl(url):
    if url.startswith('//'):
        url='http:'+url
    if url.startswith('www'):
        url='http://'+url
    return url	
def xtream_get_conf():
    multi_tab=[]
    xuser = config.plugins.iptvplayer.ts_xtream_user.value
    xpass = config.plugins.iptvplayer.ts_xtream_pass.value	
    xhost = config.plugins.iptvplayer.ts_xtream_host.value	
    xua = config.plugins.iptvplayer.ts_xtream_ua.value
    if ((xuser!='') and (xpass!='') and (xhost!='')):
        name_=xhost+' ('+xuser+')'
        if not xhost.startswith('http'): xhost='http://'+xhost
        multi_tab.append((name_,xhost,xuser,xpass,xua))
    
    xtream_conf_path='/etc/tsiplayer_xtream.conf'
    if os.path.isfile(xtream_conf_path):
        with open(xtream_conf_path) as f: 
            for line in f:
                line=line.strip()
                name_,ua_,host_,user_,pass_= '','','','',''
                _data = re.findall('(.*?//.*?)/.*?username=(.*?)&.*?password=(.*?)&',line, re.S)			
                if _data: name_,host_,user_,pass_= _data[0][0]+' ('+_data[0][1]+')',_data[0][0],_data[0][1],_data[0][2]
                else:
                    _data = re.findall('(.*?)#(.*?)#(.*?)#(.*?)#(.*)',line, re.S) 
                    if _data: name_,host_,user_,pass_,ua_= _data[0][0],_data[0][1],_data[0][2],_data[0][3],_data[0][4]
                    else:
                        _data = re.findall('(.*?)#(.*?)#(.*?)#(.*)',line, re.S) 
                        if _data: name_,host_,user_,pass_= _data[0][0],_data[0][1],_data[0][2],_data[0][3]															
                if ((user_!='') and (pass_!='') and (host_!='')):
                    if not host_.startswith('http'): host_='http://'+host_
                    multi_tab.append((name_,host_,user_,pass_,ua_))
    return 	multi_tab




class TsThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
    def run(self):
        self._target(*self._args)

class TSCBaseHostClass:
    def __init__(self, params={}):
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive'}
        if '' != params.get('cookie', ''):
            self.COOKIE_FILE = GetCookieDir(params['cookie'])
            self.defaultParams = {'header':self.HEADER,'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        else:
            self.defaultParams = {'header':self.HEADER}
        self.sessionEx = MainSessionWrapper() 
        self.up = urlparser()
        self.ts_urlpars = ts_urlparser()
        proxyURL = params.get('proxyURL', '')
        useProxy = params.get('useProxy', False)
        self.cm = common(proxyURL, useProxy)
        self.currList = []
        self.currItem = {}
        if '' != params.get('history', ''):
            self.history = CSearchHistoryHelper(params['history'], params.get('history_store_type', False))
        self.moreMode = False
        self.TrySetMainUrl = True
        
    def set_MAIN_URL(self):
        if self.TrySetMainUrl:
            sts, data = self.getPage(self.MAIN_URL)
            url = data.meta['url']
            if url.endswith('/'): url = url[:-1]
            printDBG('NEw URL = '+url)
            self.MAIN_URL = url
            self.TrySetMainUrl = False
            
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        baseUrl=self.std_url(baseUrl)
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)

    def get_url_page(self,url,page,type_=1):
        if page > 1:
            if type_==1:
                url=url+'/page/'+str(page)
                url = url.replace('//page','/page')
        return url

    def start(self,cItem):
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu(cItem)
        elif mode=='10':
            self.showmenu1(cItem)	
        elif mode=='11':
            self.showmenu2(cItem)
        elif mode=='19':
            self.showfilter(cItem)                    
        elif mode=='20':
            self.showitms(cItem)
        elif mode=='21':
            self.showelms(cItem)		
        return True
        
    def add_menu(self, cItem, pat1, pat2, data, mode_,s_mode=[], del_=[], TAB=[], search=False, Titre='',ord=[0,1],Desc=[],Next=[0,0],u_titre=False,ind_0=0,local=[],resolve='0',EPG=False,corr_=True,pref_='',post_data='',pat3='',ord3=[0,1],LINK='',hst='tshost',add_vid=True,image_cook=[False,{}],year_op=0,del_titre=''):
        if isinstance(mode_, str):
            mode = mode_
        else:
            mode = ''
        printDBG('start_add_menu, URL = '+cItem.get('url',self.MAIN_URL) )
        page=cItem.get('page',1)
        data_out  = ''
        found = False
        TAB0  = []
        elms_   = []
        if TAB!=[]:
            if Titre!='':
                self.addMarker({'category':'Marker','title': tscolor('\c00????30') + Titre,'icon':cItem['icon']})
            for (titre,url,mode,sub_mode) in TAB:
                if url.startswith('/'): url = self.MAIN_URL+url
                self.addDir({'category':'host2', 'title': titre,'mode':mode,'sub_mode':sub_mode,'url':url,'import':cItem['import'],'icon':cItem['icon']})
        else:
            if data=='':
                if LINK == '': LINK = cItem.get('url',self.MAIN_URL) 
                if LINK == '': LINK = self.MAIN_URL
                if LINK.startswith('//'): LINK = 'https:'+LINK
                if LINK.startswith('/'): LINK = self.MAIN_URL+LINK				
                if ((Next[0]==1) and (page>1)): LINK=cItem['url']+'/page/'+str(page)
                printDBG('link4:'+LINK)
                
                if post_data !='':
                    sts, data = self.getPage(LINK,post_data=post_data)
                else:
                    sts, data = self.getPage(LINK)
                if not sts: data=''
            #printDBG('DATA:'+data)
            if pat1 !='':
                data0=re.findall(pat1, data, re.S)
            else:
                data0 = [data,]
            if data0:
                if (len(data0)>ind_0) or (ind_0 == -1):
                    if pat2 !='':
                        #printDBG('pat2:'+pat2)
                        data1=re.findall(pat2, data0[ind_0], re.S)
                        #printDBG('data1:'+str(data1))
                        if ((not data1) and (pat3!='')):
                            ord = ord3
                            data1=re.findall(pat3, data0[ind_0], re.S)	
                    else:
                        data1 = [data0[ind_0],]	                                                      
                    
                        
                    if data1 and (Titre!=''):
                        self.addMarker({'title': tscolor('\c00????30') + Titre,'icon':cItem['icon']})
                    if mode=='desc': 
                        desc = ''
                        for (tag,pat,frst,Del_0) in Desc:
                            if desc == '': frst = ''
                            elif frst == '': frst = ' | '
                            if data1:
                                desc_=re.findall(pat, data1[0], re.S)	
                                if desc_:
                                    if ((Del_0=='') or ((Del_0!='') and (Del_0.lower() not in desc_[0].lower()))):
                                        if self.cleanHtmlStr(desc_[0]).strip()!='':
                                            desc = desc + frst + tscolor('\c00????00') + tag + ': ' + tscolor('\c00??????') + self.cleanHtmlStr(desc_[0])
                        return desc
                    elif mode=='param_servers':
                        for elm in data1:
                            titre = elm[ord[0]]
                            x = range(1, len(ord))
                            params = ''
                            for i in x:
                                params = params + elm[ord[i]]+'%%'                       
                            TAB0.append({'name':self.cleanHtmlStr(titre), 'url':'hst#tshost#'+params, 'need_resolve':1})
                        return (data,TAB0)
                    for elm in data1:
                        if len(ord)==2:
                            if mode.startswith('data_out0'):
                                url   = ''
                                titre = elm[ord[0]]
                                image = cItem.get('icon','')
                                desc  = cItem.get('desc','')
                                data_out  = elm[ord[1]]
                                #printDBG('data_out0='+data_out)
                            elif mode.startswith('data_out'):
                                url   = elm[ord[0]]
                                titre = elm[ord[1]]
                                image = cItem.get('icon','')
                                desc  = cItem.get('desc','')
                                data_out  = elm[2]
                                #printDBG('data_out1='+data_out)
                            else:
                                url   = elm[ord[0]]
                                titre = elm[ord[1]]
                                image = cItem.get('icon','')
                                desc  = cItem.get('desc','')
                        elif len(ord)==3:
                            url   = elm[ord[0]]
                            titre = elm[ord[1]]
                            if elm[ord[2]] !=-1: image = self.std_url(elm[ord[2]])
                            else: image = cItem.get('icon','')
                            desc  = cItem.get('desc','')
                        elif len(ord)>3:
                            url   = elm[ord[0]]
                            titre = elm[ord[1]]
                            if elm[ord[2]] !=-1: image = self.std_url(elm[ord[2]])
                            else: image = cItem.get('icon','')
                            x = range(3, len(ord))
                            desc0 = ''
                            for i in x:
                                desc0  = desc0 + elm[ord[i]]					
                            desc = ''
                            for (tag,pat,frst,Del_0) in Desc:
                                if desc == '': frst = ''
                                elif frst == '': frst = ' | '
                                desc_=re.findall(pat, desc0, re.S)	
                                if desc_:
                                    if ((Del_0=='') or ((Del_0!='') and (Del_0.lower() not in desc_[0].lower()))):
                                        if self.cleanHtmlStr(desc_[0]).strip()!='':
                                            desc = desc + frst + tscolor('\c00????00') + tag + ': ' + tscolor('\c00??????') + self.cleanHtmlStr(desc_[0])
                        sub_mode=0
                        if del_titre!='': titre = re.sub(del_titre,'',titre)
                        for (elm_0,elm_1) in s_mode:
                            if elm_0 in url: sub_mode=elm_1
                        if corr_:
                            if pref_!='': url = pref_+url
                            else:
                                if   url.startswith('http'): url = url
                                elif url.startswith('//'): url = 'https:'+url
                                elif url.startswith('/'): url = self.MAIN_URL+url
                                else: url = self.MAIN_URL+'/'+url
                        if mode.startswith('serv'): 
                            Local = ''
                            need_resolve = 1							
                            if mode == 'serv_url':
                                if url.startswith('http'):
                                    titre = self.up.getDomain(url, onlyDomain=True)
                                else:
                                    titre=''                            
                            if resolve == '1': URL = 'hst#tshost#'+url
                            else: URL = url 
                            for elm__ in local:
                                if elm__[0] in url:
                                    Local = 'local'
                                    if 'TRAILER' in elm__[1]: titre = '|Trailer| '+elm__[1].replace('TRAILER','').strip()
                                    elif '#0#' in elm__[1]:
                                        titre = elm__[1].replace('#0#','').strip()
                                        Local = ''
                                    else:
                                        if titre!='': titre = '|Local| '+elm__[1]+' - '+titre
                                        else: titre = '|Local| '+elm__[1]
                                    if elm__[2] == '1':
                                        URL = 'hst#tshost#'+url
                                    elif elm__[2] == '2':
                                        URL = url
                                        need_resolve = 0
                                    else:
                                        URL = url
                            if '!!DELETE!!' not in titre:
                                TAB0.append({'name':self.cleanHtmlStr(titre), 'url':URL, 'need_resolve':need_resolve,'type':Local})
                        elif mode.startswith('link'):
                            url = url.replace('\\/','/')
                            url = url.replace('\\','')
                            if mode=='link4':
                                TAB0.append((titre+'|'+url,'4'))
                            elif mode=='link1':
                                TAB0.append((url,'1'))
                        else:
                            
                            if image.startswith('/'): image = self.MAIN_URL+image
                            if image_cook[0]: image = strwithmeta(image,image_cook[1])
                            if '\\u0' in titre:
                                titre = titre.decode('unicode_escape',errors='ignore')
                            titre = self.cleanHtmlStr(str(titre))
                            if not any(word in titre for word in del_):
                                if u_titre:
                                    desc1,titre = self.uniform_titre(titre,year_op)
                                    desc = desc1 + desc                             
                                if (titre!='') and (url!=''):
                                    if isinstance(mode_, str):
                                        mode = mode_
                                    else:
                                        for (tag,md,tp) in mode_:
                                            if tp == 'URL': str_cnt = url
                                            else: str_cnt = titre
                                            if tag=='': mode = md
                                            elif tag in str_cnt: mode = md 
                                    printDBG('link0000:'+mode+'|'+url)
                                    if mode=='video':
                                        found = True
                                        eelm = {'category':'host2','good_for_fav':True, 'title': titre,'sub_mode':sub_mode,'url':url, 'desc':desc,'import':cItem['import'],'icon':image,'hst':hst,'EPG':EPG}
                                        self.addVideo(eelm)	
                                        elms_.append(eelm)
                                    elif mode=='picture':
                                        found = True
                                        self.addPicture({'category':'host2','good_for_fav':True, 'title': titre,'sub_mode':sub_mode,'url':url, 'desc':desc,'import':cItem['import'],'icon':image,'hst':hst,'EPG':EPG})	
                                    else:	
                                        #printDBG('link0000:'+url)
                                        eelm = {'category':'host2','good_for_fav':True, 'title': titre,'sub_mode':sub_mode,'mode':mode.replace('data_out:','').replace('data_out0:',''),'url':url, 'desc':desc,'import':cItem['import'],'icon':image,'hst':'tshost','EPG':EPG,'data_out':data_out}
                                        self.addDir(eelm)
                                        elms_.append(eelm)
                    if ((Next[0]==1) or (Next[0]==2)) and (Next[1]!='none'):
                        self.addDir({'import':cItem['import'],'name':'categories', 'category':'host2', 'url':cItem['url'], 'title':'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':cItem['icon'], 'mode':Next[1]})	
                    elif (Next[0]!=0) and (Next[1]!='none'):
                        next_=re.findall(Next[0], data, re.S)	
                        if next_:
                            URL_=next_[0]
                            if corr_:
                                if pref_!='': URL_ = pref_+URL_
                                else:
                                    if   URL_.startswith('http'): URL_ = URL_
                                    elif URL_.startswith('/'): URL_ = self.MAIN_URL+URL_
                                    else: URL_ = self.MAIN_URL+'/'+URL_
                            self.addDir({'import':cItem['import'],'name':'categories', 'category':'host2', 'url':URL_, 'title':'Page Suivante', 'page':1, 'desc':'Page Suivante', 'icon':cItem['icon'], 'mode':Next[1]})	
            if (mode=='video') and (not found) and (add_vid):
                self.addVideo({'category':'host2','good_for_fav':True, 'title': cItem['title'],'url':cItem['url'], 'desc':cItem.get('desc',''),'import':cItem['import'],'icon':cItem['icon'],'hst':'tshost','EPG':EPG})						
        if search:
            self.addDir({'category':'search'  ,'title':tscolor('\c00????30') + _('Search'),'search_item':True,'page':1,'hst':'tshost','import':cItem['import'],'icon':cItem['icon']})
        printDBG('elms_='+str(elms_))
        return (data,TAB0,elms_)	




    def std_host_name(self,name_, direct=False):
        if '|' in name_:
            n1 = name_.split('|')[-1]
            n2 = name_.replace(name_.split('|')[-1],'')
            if direct=='direct': name_=n2+tscolor('\c0090??20')+n1.replace('embed.','').title()
            elif self.ts_urlpars.checkHostSupportbyname(n1):
                name_=n2+tscolor('\c0090??20')+n1.replace('embed.','').title()	
            elif self.ts_urlpars.checkHostNotSupportbyname(n1):
                name_=n2+tscolor('\c00??1020')+n1.replace('embed.','').title()
            else:
                name_=n2+tscolor('\c00999999')+n1.replace('embed.','').title()                	
        else: 
            if direct=='direct': name_=tscolor('\c0090??20')+name_.replace('embed.','').title()
            elif self.ts_urlpars.checkHostSupportbyname(name_):
                name_=tscolor('\c0090??20')+name_.replace('embed.','').title()
            elif self.ts_urlpars.checkHostNotSupportbyname(name_):
                name_=tscolor('\c00??5050')+name_.replace('embed.','').title()	
              
                                
        return name_ 
        
    def std_url(self,url):
        url1=url
        printDBG('url0='+url1)
        if '\u0' in url1: url1 = str(url1.decode('unicode_escape',errors='ignore'))
        url1=url1.replace('\\/','/')     
        url1=url1.replace('://','rgy11soft')
        url1=url1.replace('?','rgy22soft')        
        url1=url1.replace('&','rgy33soft') 
        url1=url1.replace('=','rgy44soft') 
        url1=urllib.unquote(url1)
        url1=urllib.quote(url1)
        url1=url1.replace('rgy11soft','://')
        url1=url1.replace('rgy22soft','?')        
        url1=url1.replace('rgy33soft','&') 	
        url1=url1.replace('rgy44soft','=') 		
        printDBG('url1='+url1)
        return url1
        
    def std_url1(self,url):
        return url.encode('utf-8')       
        
    def uniform_titre(self,titre,year_op=0):
        titre=titre.replace('مشاهدة وتحميل مباشر','').replace('مشاهدة','').replace('اون لاين','')
        tag_type   = ['مدبلج للعربية','مترجمة للعربية','مترجم للعربية', 'مدبلجة', 'مترجمة' , 'مترجم' , 'مدبلج', 'مسلسل', 'عرض', 'انمي', 'فيلم']
        tag_qual   = ['1080p','720p','WEB-DL','BluRay','DVDRip','HDCAM','HDTC','HDRip', 'HD', '1080P','720P','DVBRip','TVRip','DVD','SD']
        tag_saison = [('الموسم الثاني','02'),('الموسم الاول','01'),('الموسم الثالث','03'),('الموسم الرابع','04'),('الموسم الخامس','05'),('الموسم السادس','06'),('الموسم السابع','07'),('الموسم الثامن','08'),('الموسم التاسع','09'),('الموسم العاشر','10')]
        type_ = tscolor('\c00????00')+ 'Type: '+tscolor('\c00??????')
        qual = tscolor('\c00????00')+ 'Quality: '+tscolor('\c00??????')
        sais = tscolor('\c00????00')+ 'Saison: '+tscolor('\c00??????')
        desc=''
        saison=''
        
        for elm in tag_saison:
            if elm[0] in titre:
                sais=sais+elm[1]
                titre = titre.replace(elm[0],'')
                break
                
        for elm in tag_type:
            if elm in titre:
                titre = titre.replace(elm,'')
                type_ = type_+elm+' | '
        for elm in tag_qual:
            if elm in titre:
                #re_st = re.compile(re.escape(elm.lower()), re.IGNORECASE)
                #titre=re_st.sub('', titre)
                titre = titre.replace(elm,'')
                qual = qual+elm+' | '
                
        data = re.findall('((?:19|20)\d{2})', titre, re.S)
        if data:
            year_ = data[-1]
            year_out = tscolor('\c0000????')+data[-1]+tscolor('\c00??????')
            if year_op==0:
                titre = year_out+'  '+titre.replace(year_, '')
                desc = 	tscolor('\c00????00')+ 'Year: '+tscolor('\c00??????')+year_+'\n'
            elif year_op==-1:
                titre = year_out+'  '+titre.replace(year_, '')
                desc = 	''			
            elif year_op==1:
                titre = titre.replace(year_, '')
                desc = 	tscolor('\c00????00')+ 'Year: '+tscolor('\c00??????')+year_+'\n'
            elif year_op==2:	
                titre = titre.replace(year_, '')
                desc = 	year_
                    
        if year_op<2:
            if sais != tscolor('\c00????00')+ 'Saison: '+tscolor('\c00??????'):
                desc = desc+sais+'\n'				
            if type_!=tscolor('\c00????00')+ 'Type: '+tscolor('\c00??????'):
                desc = desc+type_[:-3]+'\n'
            if qual != tscolor('\c00????00')+ 'Quality: '+tscolor('\c00??????'):
                desc = desc+qual[:-3]+'\n'

        pat = 'موسم.*?([0-9]{1,2}).*?حلقة.*?([0-9]{1,2})'
        data = re.findall(pat, titre, re.S)
        if data:
            sa = data[0][0]
            ep = data[0][1]
            if len(sa)==1: sa='0'+sa
            if len(ep)==1: ep='0'+ep			
            ep_out = tscolor('\c0000????')+'S'+sa+tscolor('\c0000????')+'E'+ep+tscolor('\c00??????')
            titre = ep_out+' '+re.sub(pat,'',titre)
            
            
        return desc,self.cleanHtmlStr(titre).replace('()','').strip()

    def MediaBoxResult(self,str_ch,year_,extra):
        urltab=[]
        str_ch_o = str_ch
        str_ch = urllib.quote(str_ch_o+' '+year_)
        result = self.SearchResult(str_ch,1,'')
        if result ==[]:
            str_ch = urllib.quote(str_ch_o)
            result = self.SearchResult(str_ch,1,'')
        for elm in result:
            titre     = elm['title']
            url       = elm['url']
            desc      = elm.get('desc','')
            image     = elm.get('icon','')
            mode      = elm.get('mode','') 
            type_     = elm.get('type','')
            sub_mode  = elm.get('sub_mode','') 
            if str_ch_o.lower().replace(' ','') == titre.replace('-',' ').replace(':',' ').lower().replace(' ',''):
                trouver = True
            else:
                trouver = False
            name_eng='|'+tscolor('\c0060??60')+self.SiteName+tscolor('\c00??????')+'| '+titre				
            if type_=='video':
                cat= 'video'
            else:
                cat = 'host2'
            element = {'titre':titre,'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':cat, 'url':url, 'title':name_eng, 'desc':desc, 'icon':image,'sub_mode':sub_mode, 'mode':mode}
            if trouver:
                urltab.insert(0, element)					
            else:
                urltab.append(element)	
        return urltab
        
    def informAboutGeoBlockingIfNeeded(self, country, onlyOnce=True):
        try: 
            if onlyOnce and self.isGeoBlockingChecked: return
        except Exception: 
            self.isGeoBlockingChecked = False
        sts, data = self.cm.getPage('https://dcinfos.abtasty.com/geolocAndWeather.php')
        if not sts: return
        try:
            data = json_loads(data.strip()[1:-1], '', True)
            if data['country'] != country:
                message = _('%s uses "geo-blocking" measures to prevent you from accessing the services from outside the %s Territory.') 
                GetIPTVNotify().push(message % (self.getMainUrl(), country), 'info', 5)
            self.isGeoBlockingChecked = True
        except Exception: printExc()
    
    def listsTab(self, tab, cItem, type='dir'):
        defaultType = type
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            type = item.get('type', defaultType)
            if type == 'dir': self.addDir(params)
            elif type == 'marker': self.addMarker(params)
            else: self.addVideo(params)

    def listSubItems(self, cItem):
        printDBG("TSCBaseHostClass.listSubItems")
        self.currList = cItem['sub_items']

    def listToDir(self, cList, idx):
        return self.cm.ph.listToDir(cList, idx)
    
    def getMainUrl(self):
        return self.MAIN_URL
    
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
            return True
        return False
    
    def getFullUrl(self, url, currUrl=None):
        if currUrl == None or not self.cm.isValidUrl(currUrl):
            try:
                currUrl = self.getMainUrl()
            except Exception:
                currUrl = None
            if currUrl == None or not self.cm.isValidUrl(currUrl):
                currUrl = 'http://fake/'
        return self.cm.getFullUrl(url, currUrl)

    def getFullIconUrl(self, url, currUrl=None):
        if currUrl != None: return self.getFullUrl(url, currUrl)
        else: return self.getFullUrl(url)
        
    def getDefaulIcon(self, cItem=None):
        try:
            return self.DEFAULT_ICON_URL
        except Exception:
            pass
        return ''

    @staticmethod 
    def cleanHtmlStr(str):
        return CParsingHelper.cleanHtmlStr(str)

    @staticmethod 
    def getStr(v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''):  return v
        return default

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return

    def addMore(self, params):
        params['type'] = 'more'
        self.currList.append(params)
        return

    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return

    def addAudio(self, params):
        params['type'] = 'audio'
        self.currList.append(params)
        return

    def addPicture(self, params):
        params['type'] = 'picture'
        self.currList.append(params)
        return

    def addData(self, params):
        params['type'] = 'data'
        self.currList.append(params)
        return

    def addArticle(self, params):
        params['type'] = 'article'
        self.currList.append(params)
        return

    def addMarker(self, params):
        params['type'] = 'marker'
        self.currList.append(params)
        return

    def listsHistory(self, baseItem={'name': 'history', 'category': 'Wyszukaj'}, desc_key='plot', desc_base=(_("Type: ")) ):
        list = self.history.getHistoryList()
        for histItem in list:
            plot = ''
            try:
                if type(histItem) == type({}):
                    pattern     = histItem.get('pattern', '')
                    search_type = histItem.get('type', '')
                    if '' != search_type: plot = desc_base + _(search_type)
                else:
                    pattern     = histItem
                    search_type = None
                params = dict(baseItem)
                params.update({'title': pattern, 'search_type': search_type,  desc_key: plot})
                self.addDir(params)
            except Exception: printExc()

    def getFavouriteData(self, cItem):
        try:
            return json_dumps(cItem)
        except Exception: 
            printExc()
        return ''

    def getLinksForFavourite(self, fav_data):
        try:
            if self.MAIN_URL == None:
                self.selectDomain()
        except Exception: 
            printExc()
        links = []
        try:
            cItem = json_loads(fav_data)
            links = self.getLinksForItem(cItem)
        except Exception: printExc()
        return links

    def setInitListFromFavouriteItem(self, fav_data):
        try:
            if self.MAIN_URL == None:
                self.selectDomain()
        except Exception: 
            printExc()
        try:
            params = json_loads(fav_data)
        except Exception: 
            params = {}
            printExc()
            return False
        self.currList.append(params)
        return True

    def getLinksForItem(self, cItem):
        # for backward compatibility
        return self.getLinksForVideo(cItem)

    def markSelectedLink(self, cacheLinks, linkId, keyId='url', marker="*"):
        # mark requested link as used one
        if len(cacheLinks.keys()):
            for key in cacheLinks:
                for idx in range(len(cacheLinks[key])):
                    if linkId in cacheLinks[key][idx][keyId]:
                        if not cacheLinks[key][idx]['name'].startswith(marker):
                            cacheLinks[key][idx]['name'] = marker + cacheLinks[key][idx]['name'] + marker
                        break

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        self.moreMode = False
        if 0 == refresh:
            if len(self.currList) <= index:
                return
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
        if 2 == refresh: # refresh for more items
            printDBG(">> endHandleService index[%s]" % index)
            # remove item more and store items before and after item more
            self.beforeMoreItemList = self.currList[0:index]
            self.afterMoreItemList = self.currList[index+1:]
            self.moreMode = True
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]

    def endHandleService(self, index, refresh):
        if 2 == refresh: # refresh for more items
            currList = self.currList
            self.currList = self.beforeMoreItemList
            for item in currList:
                if 'more' == item['type'] or (item not in self.beforeMoreItemList and item not in self.afterMoreItemList):
                    self.currList.append(item)
            self.currList.extend(self.afterMoreItemList)
            self.beforeMoreItemList = []
            self.afterMoreItemList  = []
        self.moreMode = False
    
