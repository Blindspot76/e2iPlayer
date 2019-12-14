# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,resolve_liveFlash,resolve_zony,tscolor
from Plugins.Extensions.IPTVPlayer.libs import ph
import re,requests

def getinfo():
	info_={}
	info_['name']='Coolkora.Com'
	info_['version']='1.0 17/06/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'#2
	info_['desc']='موقع للبث المباشر ونقل المباريات'
	info_['icon']='https://i.ibb.co/BnQ90Gt/coolkora-logo.png'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'coolkora.cookie'})
		self.MAIN_URL = 'http://ar.coolkora.com'
		self.USER_AGENT = 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage

	
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'مباريات اليوم','url':'','icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'قنوات'        ,'url':'','icon':cItem['icon'],'mode':'25'})

	def showmatchs(self,cItem):
		sts,data=self.getPage('http://mobikora.tv/table')
		if sts:
			printDBG('dddddddd'+data)
			films_list = re.findall('<TABLE CLASS="league(.*?)(<TD CLASS="league"|<script>)', data, re.S)
			for (data1,x1) in films_list:
				I_list = re.findall('<img.*?src="(.*?)"', data1, re.S)
				if I_list: image=I_list[0]
				else: image=cItem['icon']
				
				I_list = re.findall('head_line">(.*?)</TD>', data1, re.S)
				if I_list: titre0=ph.clean_html(I_list[0])
				else: titre0=''
				self.addMarker({'title':tscolor('\c00????00')+titre0,'desc':'','icon':image})				
				I_list = re.findall('team_l"(.*?)(<TD CLASS="team_logo1|rgysoft)', data1+'rgysoft', re.S)
				for (data2,x2) in I_list:
					A_list = re.findall('time_style">(.*?)</.*?channels_table">(.*?)</TABLE>.*?team_name1.*?">(.*?)<.*?team_name2.*?">(.*?)<', data2, re.S)
					for (time_,data3,name1,name2) in A_list:
						time1='# ['+ph.clean_html(time_)+'] #  '+tscolor('\c0000????')
						titre=name1+' Vs '+name2
						self.addDir({'import':cItem['import'],'category' : 'host2','title':time1+titre+'  #','url':data3,'desc':'','icon':image,'mode':'21'})	
		else:
			printDBG('dddddddd1'+data)

	def showmatchs1(self,cItem):
		hst='host2'
		img_=cItem['icon']
		data=cItem['url']
		I_list = re.findall('(HREF|href)="(.*?)".*?(SRC|src)="(.*?)"', data, re.S)
		for (x1,url,x2,image) in I_list:
			I_titre = re.findall('.*/(.*?)\.', url, re.S)
			if I_titre:
				titre=I_titre[0]
			else:
				titre=url
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'desc':'','icon':image,'hst':'tshost'})	
			


	def showchaines(self,cItem):
		image=cItem['icon']
		sts,data=self.getPage(self.MAIN_URL)
		if sts:
			printDBG('dddddddd'+data)
			films_list = re.findall("<ul class='sub-menu'>(.*?)</nav>", data, re.S)
			if films_list:
				I_list = re.findall('<li.*?href=\'(.*?)\'.*?name\'>(.*?)<', films_list[0], re.S)
				for (url,titre) in I_list:
					if '/search/' not in url:
						self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'desc':'','icon':image,'hst':'tshost'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		Tab_els = re.findall('<iframe allowfullscreen.*?src="(.*?)"', data, re.S)
		if Tab_els:
			url=Tab_els[0]
		else:
			url=URL
		sts, data = self.getPage(url)
		if sts:
			Tab_els = re.findall('<div class="channel-quality"(.*?)<div class="channel', data, re.S)
			if Tab_els:
				Tab_els = re.findall('class="quality.*?href="(.*?)".*?quality-name">(.*?)</div>.*?quality-info">(.*?)</ul>', Tab_els[0], re.S)
				for (url,name1,qual) in Tab_els:
					name='# '+ph.clean_html(qual)+' # '+tscolor('\c00????00')+ph.clean_html(name1)
					urlTab.append({'name':name, 'url':'hst#tshost#'+url, 'need_resolve':1})

				
				
		return urlTab
		

	def getVideos(self,videoUrl):
		urlTab = []	
		sts, data = self.getPage(videoUrl)
		url_data = re.findall("channel='(.*?)'.*?src='(.*?\..*?)/", data, re.S)
		if url_data:
			hst=url_data[0][1]
			if 'zony' in hst: hst='http://www.zony.xyz'
			if 'ezcast' in hst: hst='http://www.embedezcast.com'
			link=hst+'/embedplayer/'+url_data[0][0]+'/1/700/400'
			printDBG('url2='+link)
			if (('zony' in link) or ('ezcast' in link)):
				urlTab.append((resolve_zony(link,videoUrl),'0'))
			else:
				urlTab.append((resolve_liveFlash(link,videoUrl),'0'))
		else:
			url_data = re.findall('<iframe w.*?src="(.*?)"', data, re.S)
			if url_data:			
				urlTab.append((url_data[0],'1'))

		return urlTab

		
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		if mode=='20':
			self.showmatchs(cItem)
		elif mode=='21':
			self.showmatchs1(cItem)
		elif mode=='25':
			self.showchaines(cItem)
