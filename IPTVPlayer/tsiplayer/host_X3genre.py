# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG,MergeDicts
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser    import urlparser as ts_urlparser

try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 
	
import re
import urllib
import cookielib
import time


###################################################
#01# HOST https://akoam.net
###################################################	
def getinfo():
	info_={}
	info_['name']=tscolor('\c0000????')+' >●★| Ramadan 2020 |★●<'
	info_['version']='1.0 26/04/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='21'
	info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
	info_['icon']='https://i.ibb.co/sWfG989/ramadan-2020.jpg'
	#info_['recherche_all']='1'
	#info_['update']='Fix Links Extract'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'tsiplayer.cookie'})
		#self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		#self.MAIN_URL = 'https://akwam.net'
		#self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		#self.AJAX_HEADER = MergeDicts(self.HEADER, {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'})
		#self.defaultParams = {'header':self.HEADER,'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.cacheLinks = {}
		#self.getPage = self.cm.getPage

	def showmenu00(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'رمضان 2020' ,'icon':cItem['icon'],'mode':'20','sub_mode':0})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'رمضان 2019' ,'icon':cItem['icon'],'mode':'20','sub_mode':1})	

	def showmenu0(self,cItem):
		sub_mode=cItem.get('sub_mode', 0)
		if sub_mode==0:
			self.addDir({'category': 'host2', 'title': 'Akwam', 'url': 'https://akwam.net/series?section=29', 'mode': '30', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_akwam import ', 'icon': 'https://i.ibb.co/0qgtD2Z/akwam.png', 'type': 'category', 'desc': ''})
			self.addDir({'category': 'host2', 'title': 'CimaNow', 'url': 'https://new.cima-now.com/category/%d8%b1%d9%85%d8%b6%d8%a7%d9%86/%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2020/', 'mode': '20', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_cimanow import ', 'type': 'category', 'icon': 'https://i.ibb.co/mCsssTr/ramadan.png'})
			self.addDir({'category': 'host2', 'title': 'Extra-3sk | مسلسلات', 'url': 'https://extra-3sk.com/category/series-ramadan-2020', 'sub_mode': '0', 'mode': '30', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_extra3sk import ', 'type': 'category', 'icon': 'https://i.ibb.co/XzFvL81/cropped-13-270x270.png'})
			self.addDir({'category': 'host2', 'title': 'Extra-3sk | برامج', 'url': 'https://extra-3sk.com/category/programs-ramadan-2020', 'sub_mode': '0', 'mode': '30', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_extra3sk import ', 'type': 'category', 'icon': 'https://i.ibb.co/XzFvL81/cropped-13-270x270.png'})
			self.addDir({'category': 'host2', 'name': 'category', 'title': 'N300', 'url': 'http://www.n300.me/phone/Category/subCat/Ramadan2020', 'sub_mode': 1, 'mode': '30', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_n300 import ', 'desc': '\xd9\x85\xd8\xb3\xd9\x84\xd8\xb3\xd9\x84\xd8\xa7\xd8\xaa \xd8\xb1\xd9\x85\xd8\xb6\xd8\xa7\xd9\x86 2020', 'type': 'category', 'icon': 'http://www.n300.me/IMGCenter/IMGSystem/LOGO/LOGO_N300_me_200px.png'})
			self.addDir({'category': 'host2', 'mode': '30', 'name': 'category', 'title': 'ArabSeed', 'url': 'https://arabseed.net/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%B1%D9%85%D8%B6%D8%A7%D9%86-2020', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_arabseed import ', 'type': 'category', 'icon': 'https://arabseed.com/themes/arabseed/img/logo-c.png'})
			self.addDir({'category': 'host2', 'sub_mode': 'serie', 'mode': '30', 'title': 'ArbLionz', 'url': 'https://m.arblionz.tv/category/\xd9\x85\xd8\xb3\xd9\x84\xd8\xb3\xd9\x84\xd8\xa7\xd8\xaa-\xd8\xb1\xd9\x85\xd8\xb6\xd8\xa7\xd9\x86/', 'import': 'from Plugins.Extensions.IPTVPlayer.tsiplayer.host_arablionz import ', 'icon': 'https://i.ibb.co/16pJgMF/unnamed.jpg', 'type': 'category', 'page': 1, 'desc': '\xd9\x85\xd8\xb3\xd9\x84\xd8\xb3\xd9\x84\xd8\xa7\xd8\xaa \xd8\xb1\xd9\x85\xd8\xb6\xd8\xa7\xd9\x86'})

		#elif sub_mode==1:
		#	self.addDir({'import':cItem['import'],'category' : 'host2','title':'By Filtre','desc':'','icon':cItem['icon'],'mode':'22','sub_mode':sub_mode})		

			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		return True

