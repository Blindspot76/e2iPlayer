# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Components.config import config
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,cryptoJS_AES_decrypt,tscolor
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDUPME_decryptPlayerParams
from binascii import a2b_hex
from hashlib import sha256
import base64
import re
import urllib


from binascii import unhexlify
from hashlib import md5

def getinfo():
	info_={}
	info_['name']='Cimaflix.Tv'
	info_['version']='1.5 17/08/2019'
	info_['dev']='RGYSoft (Thx to SAMSAMSAM)'
	info_['cat_id']='104'#'201'
	info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
	info_['icon']='https://i.ibb.co/MM3NSMZ/cimaflix.png'
	info_['recherche_all']='0'
	info_['update']='bugs fix'
		
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'cimaflix.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.cimaflix.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Upgrade-Insecure-Requests':'1','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER,'with_metadata':True,'no_redirection':False, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):

		#sts, data = self.getPage(self.MAIN_URL)
		#if sts:
		#	Liste_els = re.findall('<a href="#"><i class="fa fa.*?>(.*?)<\/a>(.*?)<\/ul>', data, re.S)
		#	for (titre,data_) in Liste_els:
		#		self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre),'icon':cItem['icon'],'mode':'20','data':data_} )
		#self.addDir({'import':cItem['import'],'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})
		
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'الرئيسية','url':self.MAIN_URL,'icon':cItem['icon'],'mode':'30'} )
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'رمضان 2020','url':self.MAIN_URL+'/categorys/%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2020/','icon':cItem['icon'],'mode':'30'} )
		#♠self.addDir({'import':cItem['import'],'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})
		
	def showmenu1(self,cItem):
		Liste_els = re.findall('<li>.*?href="(.*?)">(.*?)<', cItem['data'], re.S)
		for (url,titre) in Liste_els:
			self.addDir({'import':cItem['import'],'category' : 'host2','url':url,'title':titre,'icon':cItem['icon'],'mode':'30'} )
			
			
	def showitms(self,cItem):
		url=cItem['url']
		page=cItem.get('page',1)
		if page>1:
			if url == self.MAIN_URL:
				url = url + '/?page='+str(page)+'/'
			else:
				url = url + 'page/'+str(page)+'/'
		
		sts, data = self.getPage(url)
		if sts:
			if '/?v=watch' in data:
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category':'host2', 'url':cItem['url']+'?v=watch','data_post':'', 'title':cItem['title'], 'desc':cItem['desc'], 'icon':cItem['icon'],'hst':'tshost'} )							
			else:
				lst_data=re.findall('MovieBlock">.*?href="(.*?)"(.*?)image:url\((.*?)\).*?Title">(.*?)<(.*?)</a>', data, re.S)
				if lst_data:
					for (url1,x1,image,name_eng,desc0) in lst_data:
						desc0 = x1+desc0
						desc1 =''
						lst_inf=re.findall('GenresList">(.*?)<div class', desc0, re.S)
						if lst_inf: desc1 = desc1 + tscolor('\c00????00')+'Genre: '+tscolor('\c00??????')+ph.clean_html(lst_inf[0])+'\n'
						lst_inf=re.findall('imdbRating">(.*?)</div>', desc0, re.S)
						if lst_inf: desc1 = desc1 + tscolor('\c00????00')+'Rate: '+tscolor('\c00??????')+ph.clean_html(lst_inf[0])+'\n'				
						desc00,name_eng = self.uniform_titre(name_eng)
						#if '://'in image: image = image.split('://')[0]+'://'+urllib.quote(image.split('://')[1])
						#else: image = cItem['image']
						desc=desc00+desc1
						self.addDir({'import':cItem['import'],'good_for_fav':True,'category':'host2', 'url':url1,'data_post':'', 'title':ph.clean_html(name_eng), 'desc':desc, 'icon':image, 'mode':'30','EPG':True,'hst':'tshost'} )							
					self.addDir({'import':cItem['import'],'category':'host2', 'url':cItem['url'], 'title':tscolor('\c0000??00')+'Next', 'page':page+1, 'desc':'Page Suivante', 'icon':cItem['icon'], 'mode':'30'})	
	
	
				
	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			printDBG('ddddddddaaaaaaaat'+data)
			data_els = re.findall('(class="serverslist active"|class="serverslist").*?data-server="(.*?)">(.*?)<', data, re.S)
			for (x1,data_,host_) in data_els:
				host_ = host_.replace(' ','')
				if not config.plugins.iptvplayer.ts_dsn.value:
					urlTab.append({'name':host_, 'url':'hst#tshost#'+data_, 'need_resolve':1})		
				else:
					urlTab0=self.getVideos(data_)
					for elm in urlTab0:
						printDBG('elm='+str(elm))
						url_ = elm[0]
						type_ = elm[1]
						if type_ == '0':
							urlTab.append({'name':self.up.getDomain(url_), 'url':url_, 'need_resolve':0})
						elif type_ == '4':	
							urlTab.append({'name':url_.split('|')[0], 'url':url_.split('|')[1], 'need_resolve':0})
						elif type_ == '1':		
							urlTab.append({'name':self.up.getDomain(url_), 'url':url_, 'need_resolve':1})
		return urlTab
		
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		str_='getsource.php?key='
		try:
			data = urllib.unquote(videoUrl)
			data = json_loads(data.strip())
			ciphertext = base64.b64decode(data['ct'])
			iv = unhexlify(data['iv'])
			salt = unhexlify(data['s'])
			b = "Fex-XFa_x3MjW4w"
			decrypted = cryptoJS_AES_decrypt(ciphertext, b, salt)
			cUrl = decrypted.replace('\\','').replace('"','')
			sts, data = self.getPage(cUrl,dict(self.defaultParams))
			if sts:
				cUrl = data.meta['url']
				if 'beeload.php' in cUrl:
					sts, data = self.getPage(cUrl,dict(self.defaultParams))
					if sts:
						lst_dat2=re.findall('eval(.*?)</script>', data, re.S)				
						if lst_dat2:
							packed = 'eval'+lst_dat2[0].strip()
							printDBG('ppppppp#'+packed+'#')
							try:
								data = unpackJSPlayerParams(packed, VIDUPME_decryptPlayerParams, 1)
								printDBG(data)
							except:
								printDBG('erreur')
							lst_dat2=re.findall("='(.*?)'", data, re.S)
							if lst_dat2:
								urlTab.append((lst_dat2[0],'0'))
				
				elif 'wp-embed.php?url=' in cUrl:
					#cUrl = cUrl.replace('wp-embed.php?url=','getsource.php?key=')
					cUrl = cUrl.replace('wp-embed.php?url=',str_)
					
					sts, data = self.getPage(cUrl,dict(self.defaultParams))
					if sts:
						lst_dat2=re.findall('file".*?"(.*?)".*?label".*?"(.*?)"', data, re.S)
						for (url,label) in lst_dat2:
							urlTab.append((label+'|'+url,'4'))
				
				else:
					urlTab.append((cUrl,'1'))
		except:
			urlTab = []
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("cima4u.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem.get('desc','')
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat2=re.findall('<div class="field">.*?title">(.*?)<.*?>(.*?)</div>', data, re.S)
			for (x1,x2) in lst_dat2:
				if 'اسم فيلم'    in x1: otherInfo1['original_title'] = ph.clean_html(x2)
				if 'اسم مسلسل'   in x1: otherInfo1['original_title'] = ph.clean_html(x2)
				if 'اسم سلسلة'   in x1: otherInfo1['original_title'] = ph.clean_html(x2)
				if 'اسم برنامج'  in x1: otherInfo1['original_title'] = ph.clean_html(x2)
				if 'اسماء اخرى'  in x1: otherInfo1['alternate_title'] = ph.clean_html(x2)			
				if 'الجودة'      in x1: otherInfo1['quality'] = ph.clean_html(x2)					
				if 'عدد حلقات'   in x1: otherInfo1['episodes'] = ph.clean_html(x2)	
				if 'تصنيف'       in x1: otherInfo1['genres'] = ph.clean_html(x2)
				if 'النوع'       in x1: otherInfo1['categories'] = ph.clean_html(x2)			
				if 'منتج'        in x1: otherInfo1['creator'] = ph.clean_html(x2)					
				if 'العمري'      in x1: otherInfo1['type'] = ph.clean_html(x2)			
				if 'حالة'        in x1: otherInfo1['status'] = ph.clean_html(x2)			
				if 'تاريخ'       in x1: otherInfo1['year'] = ph.clean_html(x2)					
				if 'قصة'         in x1: desc = ph.clean_html(x2)			
			
				
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)

			
