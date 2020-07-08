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
import hashlib
import urllib,cookielib,time
import threading

black,white,gray='\c00000000','\c00??????','\c00808080'
blue,green,red,yellow,cyan,magenta='\c000000??','\c0000??00','\c00??0000','\c00????00','\c0000????','\c00??00??'

tunisia_gouv = [("", "None"),("Tunis","Tunis"),("Ariana","Ariana"),("Béja","Béja"),("Ben Arous","Ben Arous"),("Bizerte","Bizerte"),\
                ("Gab%E8s","Gabès"),("Gafsa","Gafsa"),("Jendouba","Jendouba"),("Kairouan","Kairouan"),("Kasserine","Kasserine"),\
                ("Kébili","Kébili"),("Kef","Kef"),("Mahdia","Mahdia"),("Manouba","Manouba"),("Médnine","Médnine"),\
                ("Monastir","Monastir"),("Nabeul","Nabeul"),("Sfax","Sfax"),("Sidi Bouzid","Sidi Bouzid"),("Siliana","Siliana"),\
                ("Sousse","Sousse"),("Tataouine","Tataouine"),("Tozeur","Tozeur"),("Zaghouane","Zaghouane")]


def printD(x1,x2=''):
	printDBG(x1)
	return ''

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
        if '' != params.get('cookie', ''):
            self.COOKIE_FILE = GetCookieDir(params['cookie'])
        self.moreMode = False

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
				
		data = re.findall('((19|20)\d{2})', titre, re.S)
		if data:
			year_ = data[0][0]
			year_out = tscolor('\c0000????')+data[0][0]+tscolor('\c00??????')
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
    
