# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
except:
	pass
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import unhexlify
from hashlib import md5
import base64
import re
import cookielib
import time
import urllib

def getinfo():
	info_={}
	info_['name']='Movs4u.Tv'
	info_['version']='1.9.1 23/02/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات اجنبية'
	info_['icon']='https://i.ibb.co/8Pgs99g/Sans-titre.png'
	info_['recherche_all']='1'
	info_['update']='Fixe trailer'	
	return info_
	
def cryptoJS_AES_decrypt(encrypted, password, salt):
    def derive_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = ''
        while len(d) < key_length + iv_length:
            d_i = md5(d_i + password + salt).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length+iv_length]
    bs = 16
    key, iv = derive_key_and_iv(password, salt, 32, 16)
    cipher = AES_CBC(key=key, keySize=32)
    return cipher.decrypt(encrypted, iv)
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		
		TSCBaseHostClass.__init__(self,{'cookie':'movs4u.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.movs4u.ws'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage
		
	def getPage(self, baseUrl, addParams = {}, post_data = None):
		baseUrl=self.std_url(baseUrl)
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)


	def getPage1(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams) 
		sts, data = self.cm.getPage(baseUrl,addParams,post_data)
		if not data: data=''
		if '!![]+!![]' in data:
			try:
				printDBG('Start CLoudflare  Vstream methode')
				oRequestHandler = cRequestHandler(baseUrl)
				if post_data:
					post_data_vstream = ''
					for key in post_data:
						if post_data_vstream=='':
							post_data_vstream=key+'='+post_data[key]
						else:
							post_data_vstream=post_data_vstream+'&'+key+'='+post_data[key]					
					oRequestHandler.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
					oRequestHandler.addParametersLine(post_data_vstream)					
				data = oRequestHandler.request()
				sts = True
				printDBG('cook_vstream_file='+self.up.getDomain(baseUrl).replace('.','_'))
				cook = GestionCookie().Readcookie(self.up.getDomain(baseUrl).replace('.','_'))
				printDBG('cook_vstream='+cook)
				if ';' in cook: cook_tab = cook.split(';')
				else: cook_tab = cook
				cj = self.cm.getCookie(self.COOKIE_FILE)
				for item in cook_tab:
					if '=' in item:	
						printDBG('item='+item)		
						cookieKey, cookieValue = item.split('=')
						cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=cookieValue, port=None, port_specified=False, domain='.'+self.cm.getBaseUrl(baseUrl, True), domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=time.time()+3600*48, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
						cj.set_cookie(cookieItem)
				cj.save(self.COOKIE_FILE, ignore_discard = True)
			except Exception, e:
				printDBG('ERREUR:'+str(e))
				printDBG('Start CLoudflare  E2iplayer methode')
				addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
				sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)	
		return sts, data



		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		Movs4u_TAB =  [{'category':'host2' ,       'title': 'Films',                  'url':self.MAIN_URL+'/movie/'      ,'icon':img_,'mode':'20'},
						{'category':'host2',       'title': 'Series','sub_mode':'serie'  ,'Url':self.MAIN_URL+'/tvshows/'    ,'icon':img_,'page':1,'mode':'30'},
						{'category':'search',      'title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'       ,'icon':img_},
						]
		self.listsTab(Movs4u_TAB, {'import':cItem['import'],'name':'host2'})
	def showmenu1(self,cItem):
		Movs4u_Film_CAT_TAB = [{'category':'host2','title': 'Films','Url':self.MAIN_URL+'/movie/','sub_mode':'film','page':1,'mode':'30'},
							{'category':'host2','title': 'Collection Films','Url':self.MAIN_URL+'/collection/','sub_mode':'Film_coll','page':1,'mode':'30'},
							{'category':'host2','title': 'Films Par Genre','sub_mode':'film','mode':'21'},
							{'category':'host2','title': 'Films Par Qualité','sub_mode':'Film_qual','mode':'21'},
							]
		self.listsTab(Movs4u_Film_CAT_TAB, {'import':cItem['import'],'name':'host2','icon':cItem['icon']})					

	def showmenu2(self,cItem):		
		gnr=cItem['sub_mode']
		img_=cItem['icon']		
		sUrl=self.MAIN_URL
		sts, data = self.getPage(sUrl) 
		if sts:
			Liste_films_data = re.findall('class="sub-menu">(.*?)\/ul', data, re.S)
			if Liste_films_data :
				if gnr=='Film_qual':
					films_data=Liste_films_data[3]
				else:
					films_data=Liste_films_data[2]		
				Liste_films_data = re.findall('<a href="(.*?)">(.*?)<', films_data, re.S)	
				for (url,titre) in Liste_films_data:
					titre=self.cleanHtmlStr(titre)
					params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':titre,'desc':titre,'page':1,'icon':img_,'sub_mode':gnr,'mode':'30'} 
					self.addDir(params)	
		
	def showitms(self,cItem):
		page=cItem.get('page',1)
		url_=cItem['Url']
		if '?' in url_:
			x1,x2=url_.split('?',1)
			url_=x1+'page/'+str(page)+'/?'+x2
		else:
			url_=cItem['Url']+'page/'+str(page)+'/'
		printDBG('list_items_movs4u='+url_)	
		gnr=cItem['sub_mode']		
		img_=cItem['icon']
		sts, data = self.getPage(url_) 
		if sts:
			cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
			Liste_films_data = re.findall('<h1(.*?)(pagination">|<div class="copy">)', data, re.S)
			if Liste_films_data :
				films_data=Liste_films_data[0][0]	
				if gnr=='film':
					if 'trending' not in cItem['Url']:
						Liste_films_data = re.findall('<article id=.*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<.*?href="(.*?)".*?metadata">(.*?)</div>.*?texto">(.*?)<.*?genres">(.*?)</div>', films_data, re.S)	
						for (image,name_eng,qual,url,meta,desc,desc2) in Liste_films_data:
							image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
							meta_=''
							meta_data = re.findall('<span.*?>(.*?)<', meta, re.S)	
							for (mt) in meta_data:
								if meta_=='':
									meta_= mt 
								else:
									meta_= meta_ + ' | ' + mt
							desc = meta_ +'\n'+tscolor('\c0000????')+'Genre: '+tscolor('\c00??????')+ self.cleanHtmlStr(desc2)+'\n'+ desc
							name_eng=self.cleanHtmlStr(name_eng)
							params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +tscolor('\c0000????')+' ('+qual+')','desc':desc,'icon':image,'hst':'tshost'} 
							self.addVideo(params)	
					else:
						Liste_films_data = re.findall('<article id=.*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<.*?href="(.*?)"', films_data, re.S)	
						for (image,name_eng,qual,url) in Liste_films_data:
							image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
							name_eng=self.cleanHtmlStr(name_eng)
							params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +tscolor('\c0000????')+' ('+qual+')','desc':'','icon':image,'hst':'tshost'} 
							self.addVideo(params)						
				elif gnr=='Film_qual':
					Liste_films_data = re.findall('class="item".*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?type">(.*?)<', films_data, re.S)	

					for (url,image,name_eng,nat) in Liste_films_data:
						image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
						name_eng=self.cleanHtmlStr(name_eng)
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +tscolor('\c0000????')+' ('+nat+')','desc':'','icon':image,'hst':'tshost'} 
						self.addVideo(params)					
				elif gnr=='serie':
					Liste_films_data = re.findall('article id.*?src="(.*?)".*?alt="(.*?)".*?href="(.*?)".*?metadata">(.*?)"texto">(.*?)</div>(.*?)</article>', films_data, re.S)	
					for (image,name_eng,url,inf1,desc,inf2) in Liste_films_data:
						desc = tscolor('\c0000????')+'Desc: '+tscolor('\c00??????')+self.cleanHtmlStr(desc)
						inf1 = self.cleanHtmlStr(inf1.replace('</span>',' | ')+'>').strip()
						inf2 = self.cleanHtmlStr(inf2.replace('</a>',' | ')).strip()
						if inf2!='':desc=tscolor('\c0000????')+'Genre: '+tscolor('\c00??????')+inf2+'\n'+desc
						if inf1!='':desc=tscolor('\c0000????')+'Info: '+tscolor('\c00??????')+inf1+'\n'+desc
						image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
						name_eng=self.cleanHtmlStr(name_eng)
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':desc,'icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
						self.addDir(params)			 
				elif gnr=='Film_coll':
					Liste_films_data = re.findall('class="item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"', films_data, re.S)	
					for (url,image,name_eng) in Liste_films_data:
						image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
						name_eng=self.cleanHtmlStr(name_eng)
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':'','icon':image,'hst':'tshost','sub_mode':'one_film_col','page':1,'mode':'30'} 
						self.addDir(params)					
				elif gnr=='one_film_col':
					Liste_films_data = re.findall('class="item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<', films_data, re.S)	
					for (url,image,name_eng,qual) in Liste_films_data:
						image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
						name_eng=self.cleanHtmlStr(name_eng)
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +tscolor('\c0000????')+' ('+qual+')','desc':'','icon':image,'hst':'tshost'} 
						self.addVideo(params)
				elif gnr=='serie_ep':
					Liste_films_data1 = re.findall('<h2>Video trailer.*?src="(.*?)"', data, re.S)
					if Liste_films_data1:			
						params = {'import':cItem['import'],'category' : 'video','url': Liste_films_data1[0],'title':'Trailer','desc':'','icon':img_,'hst':'none'} 
						self.addVideo(params)			
					Liste_films_data = re.findall('<div id=\'seasons\'>(.*?)</script>', data, re.S)
					if Liste_films_data:
						films_data=Liste_films_data[0]
						Liste_films_data = re.findall("<span class='title'>(.*?)<(.*?)<\/ul>", films_data, re.S)
						for (season,data_s) in Liste_films_data:
							params = {'name':'categories','category' : 'video','title':tscolor('\c00????00')+season.replace('الموسم',''),'desc':'','icon':img_} 
							self.addMarker(params)
							films_data = re.findall("<li.*?src='(.*?)'.*?numerando'>(.*?)<.*?href='(.*?)'>(.*?)<", data_s, re.S)
							for (image,name_eng,url,name2) in films_data:
								image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
								name_eng=self.cleanHtmlStr(name_eng)
								params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +tscolor('\c0000????')+'  # '+name2,'desc':'','icon':image,'hst':'tshost'} 
								self.addVideo(params)
				if gnr!='serie_ep':
					params = {'import':cItem['import'],'category':'host2','title': tscolor('\c0000??00')+'Next Page','Url':cItem['Url'],'sub_mode':gnr,'page':page+1,'icon':img_,'mode':'30'}
					self.addDir(params)							

	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			Liste_films_data = re.findall('"result-item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?">(.*?)<(.*?)</article>', data, re.S)
			for (url,image,name_eng,type_,inf) in Liste_films_data:
				type_ = self.cleanHtmlStr(type_).strip()
				desc=''
				lst_inf=re.findall('rating">(.*?)</', inf, re.S)
				if lst_inf: desc = desc + tscolor('\c00????00')+'Rating: '+tscolor('\c00??????')+ph.clean_html(lst_inf[0])+'\n'
				lst_inf=re.findall('year">(.*?)</', inf, re.S)
				if lst_inf: desc = desc + tscolor('\c00????00')+'Year: '+tscolor('\c00??????')+ph.clean_html(lst_inf[0])+'\n'			
				lst_inf=re.findall('contenido">(.*?)</div', inf, re.S)
				if lst_inf: desc = desc + tscolor('\c00????00')+'Story: '+tscolor('\c00??????')+ph.clean_html(lst_inf[0])+'\n'					
				if type_=='Movie':
					params = {'import':extra,'good_for_fav':True,'category' : 'video','url': url,'title':name_eng,'desc':desc,'icon':image,'hst':'tshost'} 
					self.addVideo(params)
				else:
					params = {'import':extra,'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':desc,'icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
					self.addDir(params)	
		


	def MediaBoxResult(self,str_ch,year_,extra):
		urltab=[]
		str_ch_o = str_ch
		str_ch = urllib.quote(str_ch_o)
		url_=self.MAIN_URL+'/page/1/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			Liste_films_data = re.findall('"result-item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?">(.*?)<', data, re.S)
			for (url,image,name_eng,type_) in Liste_films_data:
				name_eng=ph.clean_html(name_eng.strip())
				desc0,titre0 = self.uniform_titre(name_eng,1)
				if str_ch_o.lower().replace(' ','') == titre0.replace('-',' ').replace(':',' ').lower().replace(' ',''):
					trouver = True
				else:
					trouver = False
				name_eng='|'+tscolor('\c0060??60')+'Movs4U'+tscolor('\c00??????')+'| '+titre0
				if type_=='Movie':
					params = {'titre':titre0,'import':extra,'good_for_fav':True,'category' : 'video','url': url,'title':name_eng,'desc':'','icon':image,'hst':'tshost'} 
					if trouver: urltab.insert(0,params)
					else: urltab.append(params)
				else:
					params = {'titre':titre0,'import':extra,'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':'','icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
					if trouver: urltab.insert(0,params)
					else: urltab.append(params)	
		return urltab

		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']
		sts, sHtmlContent = self.getPage(URL)
		if sts:
			_data0 = re.findall("'trailer'>.*?'title'>(.*?)<.*?server'>(.*?)<.*?data-post='(.*?)'",sHtmlContent, re.S)
			if _data0:
				urlTab.append({'name':_data0[0][0].replace('- تريلر الفلم',''), 'url':'hst#tshost#'+_data0[0][2], 'need_resolve':1})					
			_data = re.findall("data-url='(.*?)'.*?title'>(.*?)<.*?server'>(.*?)<",sHtmlContent, re.S)
			for (data_url,titre1,srv) in _data:
				titre1=titre1.replace('سيرفر مشاهدة رقم','Server:') 
				local=''
				if 'movs' in srv.lower(): local='local'
				srv=srv.lower().replace('openload.com','openload.co')
				tag = ''
				if '/player_c.php'  in data_url:
					tag  = ' [Aflamyz M3U8 (Mail.Ru)]'
					local='local'
				if '/main_player1.php'  in data_url:
					tag  = ' [Arabramadan MAIN]'
					local='local'	
				if '/main_player.php'  in data_url:
					tag  = ' [M3U8 MAIN (GOOGLE)]'
					local='local'					
				if '/player_y.php'  in data_url:
					tag  = ' [Aflamyz M3U8 (YANDEX)]'
					local='local'
				if '/player_ok.php' in data_url:
					tag  = ' [Aflamyz MP4 (OK.RU)]'
					local='local'
				if '/player_m.php' in data_url:
					tag  = ' [Aflamyz MP4 (MEGA)]'
					local='local'
				if '/player_j.php'  in data_url:
					tag  = ' [Arabramadan MP4 (GOOGLE)]'
					local='local'
				if '/player_e1.php'  in data_url:
					tag  = ' [Gdrive]'
					local='local'
				if '/e1.php' in data_url:
					tag  = ' [Arabramadan MP4 (GOOGLE)]'
					local='local'					
				if '/e2.php' in data_url:
					tag  = ' [Arabramadan MP4 (GOOGLE)]'
					local='local'
				if '/or/index.php' in data_url:
					tag  = ' [Aflamys MP4 ]'
					local='local'					

				urlTab.append({'name':'|'+titre1+'| '+srv+tag, 'url':'hst#tshost#'+data_url+'|'+cItem['url'], 'need_resolve':1,'type':local})		
		return urlTab

	
	def extractLink(self,videoUrl,refer):
		url_out='None'
		printDBG('a1')
		if 'juicy.php?url=' in videoUrl:
			printDBG('a3')
			_data3 = re.findall('url=(.*)',videoUrl, re.S)
			if _data3: 
				url_out = _data3[0]
		else:
			printDBG('a4')
			Params = dict(self.defaultParams)
			Params['header']['Referer']=refer
			sts, data = self.getPage(videoUrl,Params)
			if sts:
				printDBG('a5')
				_data2 = re.findall('<iframe.*?src="(.*?)"',data, re.S)		 		
				if _data2:			
					url_out = _data2[0]
				else:
					printDBG('a6')
					_data4 = re.findall('javascript">eval(.*?)</script>',data, re.S)
					if _data4:
						script_eval='eval'+_data4[0].strip()
						printDBG(script_eval)
						datau = unpackJSPlayerParams(script_eval, SAWLIVETV_decryptPlayerParams, 0)
						printDBG(datau)
						_data5 = re.findall('<iframe.*?src="(.*?)"',datau.replace('\\',''), re.S)
						if _data5:
							url_out = _data5[0]
						else:
							_data5 = re.findall('sources:(\[.*?])',datau.replace('\\',''), re.S)
							if _data5:
								url_out = _data5[0]						
					else:
						printDBG('a7='+data)
						_data4 = re.findall('"file".*?"(.*?)"',data, re.S)
						if _data4:
							printDBG('a9')
							url_out = _data4[0]						
						else:
							_data2 = re.findall('<meta.*?url=(.*?)"',data, re.S)		 		
							if _data2:			
								url_out = _data2[0]					
		return url_out	

	def getVideos(self,videoUrl):
		urlTab = []	
		refer=''
		if '|' in videoUrl:
			url_ref,refer=videoUrl.split('|')
			videoUrl = url_ref
		printDBG("1")
		if videoUrl.startswith('http'):
			i=0
			while True:
				i=i+1
				printDBG(str(i)+">>>>Start<<<< "+videoUrl)
				oldURL=videoUrl
				videoUrl = self.extractLink(videoUrl,refer)
				printDBG(str(i)+">>>>End<<<< "+videoUrl)
				if videoUrl.startswith('['):
					_data3 = re.findall('label":"(.*?)".*?file":"(.*?)"',videoUrl, re.S)	
					for (label,uurl) in _data3:
						urlTab.append((label+'|'+uurl,'4'))	
					break	
				elif videoUrl == 'None': 
					printDBG('1') 			
					urlTab.append((oldURL,'1'))
					break 				
				elif '.m3u8' in videoUrl:
					printDBG('2')
					URL1=strwithmeta(videoUrl, {'Referer':url_ref})
					urlTab.append((URL1,'3'))
					break
				elif 'arabramadan' in videoUrl:
					params = dict(self.defaultParams)
					params['header']['Referer'] = oldURL
					sts, data = self.getPage(videoUrl,params)
					if sts:
						_data3 = re.findall('JuicyCodes.Run\("(.*?)"\)',data, re.S)	
						if _data3:
							packed = base64.b64decode(_data3[0].replace('"+"',''))
							printDBG('packed'+packed)
							Unpacked = cPacker().unpack(packed)
							printDBG('packed'+Unpacked)
							meta_ = {'Referer':'https://arabramadan.com/embed/L00w0FyU0if4mHD/'}
							_data3 = re.findall('src".*?"(.*?)".*?label":"(.*?)"',Unpacked, re.S)	
							for (uurl,ttitre) in _data3:
								uurl = strwithmeta(ttitre+'|'+uurl,meta_)
								urlTab.append((uurl,'4'))
					break	
				elif 'gdriveplayer' in videoUrl:
					params = dict(self.defaultParams)
					params['header']['Referer'] = oldURL
					sts, data = self.getPage(videoUrl,params)
					if sts:
						result = re.findall('(eval\(function\(p.*?)</script>',data, re.S)	
						if result:
							data = result[0].strip()
							printDBG('eval trouver='+result[0].strip()+'#')
							data0 = cPacker().unpack(result[0].strip())
							printDBG('data0='+data0+'#')
							result = re.findall('data=.*?(\{.*?}).*?null.*?[\'"](.*?)[\'"]',data0, re.S)
							if result:
								code_ = json_loads(result[0][0])
								printDBG('Code='+str(code_))
								data1 = result[0][1].strip().replace('\\','')									
								printDBG('data1='+data1)
								lst = re.compile("[A-Za-z]{1,}").split(data1)
								printDBG('lst='+str(lst))
								script = ''
								for elm in lst:
									script = script+chr(int(elm))
								printDBG('script='+script)
								result = re.findall('pass.*?[\'"](.*?)[\'"]',script, re.S)
								if result:
									pass_ = result[0]								
									printDBG('pass_='+pass_)
									ciphertext = base64.b64decode(code_['ct'])
									iv = unhexlify(code_['iv'])
									salt = unhexlify(code_['s'])
									b = pass_
									decrypted = cryptoJS_AES_decrypt(ciphertext, b, salt)
									printDBG('decrypted='+decrypted)
									data2 = decrypted[1:-1]
									#data2 = decrypted.replace('"','').strip()
									printDBG('data2='+data2)									
									data2 = cPacker().unpack(data2)
									printDBG('data2='+data2)								
									url_list = re.findall('sources:(\[.*?\])',data2, re.S)	
									#for data3 in url_list:
									data3= url_list[0]
									data3 = data3.replace('\\','').replace('"+countcheck+"','')
									printDBG('data3='+data3+'#')
									src_lst = json_loads(data3)
									printDBG('src_lst='+str(src_lst)+'#')
									for elm in src_lst:
										_url   = elm['file']
										_label = elm.get('label','Google')
										if 'm3u8' in _url:
											urlTab.append((_url,'3'))	
										else:
											urlTab.append(('Google ('+_label+')|'+_url,'4'))															
					break
				 
				elif 'aflamyz' in videoUrl:
					params = dict(self.defaultParams)
					params['header']['Referer'] = oldURL
					sts, data = self.getPage(videoUrl,params)
					if sts:
						result = re.findall('data-en="(.*?)".*?data-p="(.*?)"',data, re.S)	
						if result:
							code_ = json_loads(urllib.unquote(result[0][0]))
							pass_ = result[0][1]
							printDBG('Code='+str(code_))
							printDBG('Pass='+pass_)
							ciphertext = base64.b64decode(code_['ct'])
							iv = unhexlify(code_['iv'])
							salt = unhexlify(code_['s'])
							b = pass_
							decrypted = cryptoJS_AES_decrypt(ciphertext, b, salt)
							printDBG('decrypted='+decrypted)
							URL = decrypted.replace('\/','/').replace('"','')
							printDBG('URL='+URL)
							params['header']['Referer'] = videoUrl
							sts, data = self.getPage(URL,params)							
							if sts:
								url_list = re.findall('"sources":(\[.*?\])',data, re.S)	
								if url_list:
									src_lst = json_loads(url_list[0])
									printDBG('src_lst='+str(src_lst)+'#')
									for elm in src_lst:
										_url   = elm['file']
										_label = elm.get('label','Aflamyz')
										if 'm3u8' in _url:
											urlTab.append((_url,'3'))	
										else:
											urlTab.append(('Aflamyz ('+_label+')|'+_url,'4'))										
					break

				elif (self.up.checkHostSupport(videoUrl) == 1):	
					printDBG('3')
					urlTab.append((videoUrl,'1'))
					break
				printDBG('4')								 									
							 					
		else:
			printDBG("2")
			post_data = {'action':'doo_player_ajax','post':videoUrl,'nume':'trailer','type':'movie'}		
			sts, data2 = self.getPage(self.MAIN_URL+'/wp-admin/admin-ajax.php', post_data=post_data)
			if sts:
				printDBG("20")
				_data0 = re.findall('<iframe.*?src="(.*?)"',data2, re.S)
				if _data0:	
					urlTab.append((_data0[0],'1'))	
		return urlTab



	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='30':
			self.showitms(cItem)			

