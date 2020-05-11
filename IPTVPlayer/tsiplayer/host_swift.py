# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Components.config import config
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs import pyaes
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes             import strwithmeta

import re,json
from hashlib import md5
from binascii import b2a_hex
import time

def getinfo():
	info_={}
	info_['name']='SwiftStream (Android App)'
	info_['version']='1.0 24/11/2019'
	info_['dev']='RGYSOFT'
	info_['cat_id']='120'
	info_['desc']='TV en streaming'
	info_['icon']='http://www.swiftstreamz.com/images/logo.png'
	info_['recherche_all']='0'
	info_['update']='New Host'
	return info_
	
def get_post_data():
	_key = "cLt3Gp39O3yvW7Gw"
	_iv = "bRRhl2H2j7yXmuk4"
	cipher = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(_key, _iv))
	ciphertext = ''
	_time = str(int(time.time()))
	_hash = md5("{0}e31Vga4MXIYss1I0jhtdKlkxxwv5N0CYSnCpQcRijIdSJYg".format(_time).encode("utf-8")).hexdigest()
	_plain = "{0}&{1}".format(_time, _hash).ljust(48).encode("utf-8")
	ciphertext += cipher.feed(_plain)
	ciphertext += cipher.feed()
	return b2a_hex(ciphertext[:-16]).decode("utf-8")
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'swift.cookie'})
		self.USER_AGENT      = 'okhttp/3.10.0'
		self.Play_User_Agent = 'Lavf/56.15.102'
		self.MAIN_URL        = 'http://swiftstreamz.com'
		Authorization        = 'Basic U3dpZnRTdHJlYW16OkBTd2lmdFN0cmVhbXpA'
		Authorization        = 'Basic QFN3aWZ0MTEjOkBTd2lmdDExIw=='		
		self.HTTP_HEADER     = {'User-Agent': self.USER_AGENT, 'Authorization' : Authorization}
		self.defaultParams   = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.base_api_url    = self.MAIN_URL+'/SwiftPanel/api.php?get_category'
		self.base_dta_url    = self.MAIN_URL+'/SwiftPanel/swiftlive.php'
		self.base_cat_url    = self.MAIN_URL+'/SwiftPanel/api.php?get_channels_by_cat_id=%s'
		self.vod_cat_url     = self.MAIN_URL+'/SwiftPanel/api.php?get_videos_by_cat_id=%s'
	def getPage(self, baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)

		 
	def showmenu0(self,cItem):
		sts, sHtmlContent = self.getPage(self.base_api_url)
		if sts:
			if 'Erreur 503' in str(sHtmlContent):
				self.addMarker({'title':'System down for maintenance','desc':'', 'icon':cItem['icon'] })	
			else:
				response = json.loads(sHtmlContent)
				for a in response['LIVETV']:
					try:
						name = a['category_name']
						id = a['cid']
						icon = a['category_image']
						try:
							if int(id)<38:
								self.addDir({'import':cItem['import'],'category':'host2', 'url':str(id), 'title':str(name), 'desc':'', 'icon':icon, 'mode':'30'})	
						except:
							pass
					except Exception:
						pass
				

	def showmenu1(self,cItem):
		id_=cItem['url']
		try:
			id_int = int(id_)
		except:
			id_int = 0
		if id_int>38: 
			url=self.vod_cat_url % (id_)
		else:
			url=self.base_cat_url % (id_)
		headers = {'Authorization': 'Basic @Swift11#:@Swift11#', 'User-Agent': self.USER_AGENT}
		Params  = {'header':headers}
		sts, sHtmlContent = self.getPage(url,Params)
		if sts:        
			items = []
			if 'Erreur 503' in str(sHtmlContent):
				self.addMarker({'title':'System down for maintenance','desc':'', 'icon':cItem['icon'] })	
			else:
				response = json.loads(sHtmlContent)
				for a in response['LIVETV']:
					streams = []
					for entry in a['stream_list']:
						if '.m3u8' in entry['stream_url'] or '.2ts' in entry['stream_url']:
							streams.append(entry)
							name = a.get('channel_title',a.get('video_title',''))
							icon = a.get('channel_thumbnail',a.get('video_thumbnail_b',''))
							url = entry['stream_url']
							token = entry['token']
							if name != entry['name']: name = name+' ('+tscolor('\c0000????')+entry['name'].strip().replace(name,'')+tscolor('\c00??????')+')'
							playencode = '%s|%s|%s' % (name, url, token)
							self.addVideo({'import':cItem['import'],'category':'video', 'url':playencode, 'title':str(name), 'desc':'', 'icon':icon,'hst':'tshost'})	
		
 	def get_links(self,cItem): 	
		urlTab = []	
		url    = cItem['url']
		tmp    = url.split('|', 2)
		title  = tmp[0]
		url    = tmp[1]
		token  = tmp[2]

		data = {"data": get_post_data()}
		try:
			token_int=int(token)
		except:
			token_int=0
		if token_int<34:
			token_url = self.MAIN_URL+'/newapptoken%s.php' % (token)
		elif token_int==34:
			token_url = self.MAIN_URL+'/vodtoken.php'
		elif token_int>34:
			token_url = self.MAIN_URL+'/newapptoken%s.php' % (token_int-1)
		headers = {'User-Agent': self.USER_AGENT}
		Params  = {'header':headers}
		printDBG('data='+str(data))
		sts, get_token = self.getPage(token_url,Params,data)		
		printDBG('get_token='+get_token)
		auth_token = get_token.partition('=')[2]
		auth_token = "".join(
			[
				auth_token[:-59],
				auth_token[-58:-47],
				auth_token[-46:-35],
				auth_token[-34:-23],
				auth_token[-22:-11],
				auth_token[-10:],
			]
		)
		url = strwithmeta(url + '?wmsAuthSign=' + auth_token ,{'User-Agent':self.Play_User_Agent})
		urlTab.append({'name':'Play', 'url':url, 'need_resolve':0})				
		return urlTab

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='30':
			self.showmenu1(cItem)
																						
