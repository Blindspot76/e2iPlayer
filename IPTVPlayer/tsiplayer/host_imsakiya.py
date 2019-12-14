# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tunisia_gouv,tscolor
from Components.config import config
import re

tunisia_gouv_code = [0,23,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24]

def getinfo():
	info_={}
	info_['name']='Prayer Time (Tunisia - Meteo.Tn)'
	info_['version']='1.0 19/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='204'
	info_['desc']='امساكية رمضان + اوقات الصلاة الرسمية للجمهورية التونسية'
	info_['icon']='http://www.meteo.tn/listefr/evenement/imsakia2013/ramadan.jpg'
	info_['warning']='Only for Tunisia'
	info_['filtre']='imsakiya_tn'
	info_['recherche_all']='0'
	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'imsakiya.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://www.meteo.tn'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):	
		#self.addDir({'category' :'host2','title':'إمساكية رمضان','icon':'http://www.meteo.tn/listefr/evenement/imsakia2019/ramadan.jpg','mode': '31'})		
		self.addDir({'category' :'host2','title':'أوقات الصلاة','icon':'https://www.newzoogle.com/wp-content/uploads/2016/03/Best-Islamic-Prayer-Times-Apps-for-Android.png','mode': '30'})		
		
			
	def showitms1(self,cItem):		
		if config.plugins.iptvplayer.imsakiya_tn.value!='':
			import datetime
			now = datetime.datetime.now()		
			Url='http://www.meteo.tn/listefr/previsions/Tunis.php'
			gouv = config.plugins.iptvplayer.imsakiya_tn.value
			post_data={'jour1':str(now.day),'mois1':str(now.month),'annee1':str(now.year),'gouv1':gouv}
			sts, data = self.getPage(Url,post_data=post_data) 
			if sts:
				Liste_cat_data = re.findall('<p class="txt12Bb1".*?>(.*?)<p.*?txt14Bb" >(.*?)<p', data, re.S)
				if Liste_cat_data:
					self.addMarker({'title':tscolor('\c00????00')+ph.clean_html(Liste_cat_data[0][0]),'desc':ph.clean_html(Liste_cat_data[0][1]),'icon':cItem['icon']})
				Liste_cat_data = re.findall('align="left" class="txt14Bb">.*?<b>(.*?)<.*?Tip\(\'(.*?)\'.*?TITLE.*?\'(.*?)\'', data, re.S)
				for (time_,desc,name_) in Liste_cat_data:
					name_=name_.replace('&nbsp;','').strip()
					time_=time_.strip()
					titre=tscolor('\c0000??00')+name_+' : '+tscolor('\c0000????')+time_
					self.addMarker({'title':titre,'desc':ph.clean_html(desc),'icon':cItem['icon']})


	def showitms2(self,cItem):		
		if config.plugins.iptvplayer.imsakiya_tn.value!='':	
			ind=0
			code_=0
			for elm in tunisia_gouv:
				if elm[0]==config.plugins.iptvplayer.imsakiya_tn.value:
					code_=tunisia_gouv_code[ind]
				ind=ind+1
			Url='http://www.meteo.tn/listear/evenement/testpage.php?gouv='+str(code_)
			printDBG('Url='+Url)
			sts, data = self.getPage(Url) 
			if sts:
				Liste_cat_data = re.findall('class="txt12Bbc">(.*?)</tr>', data, re.S)
				if Liste_cat_data:
					desc=ph.clean_html(Liste_cat_data[0])
					Liste_cat_data2 = re.findall('class=m12bvert>(.*?)</td>', data, re.S)
					if Liste_cat_data2:
						printDBG('dddddddddddddd'+str(Liste_cat_data2))
						a1,a2=Liste_cat_data2[0].split('<br>',1)
						b1,b2=Liste_cat_data2[1].split('<br>',1)
					self.addMarker({'title':tscolor('\c00????00')+'إمساكية اليوم','desc':desc,'icon':cItem['icon']})
					titre=tscolor('\c0000????')+ph.clean_html(a1)+'    '+tscolor('\c00??????')+'|    '+tscolor('\c0000??00')+ph.clean_html(a2)
					self.addMarker({'title':titre,'desc':desc,'icon':cItem['icon']})
					self.addMarker({'title':tscolor('\c00????00')+'إمساكية الغد','desc':desc,'icon':cItem['icon']})				
					titre=tscolor('\c0000????')+ph.clean_html(b1)+'    '+tscolor('\c00??????')+'|    '+tscolor('\c0000??00')+ph.clean_html(b2)
					self.addMarker({'title':titre,'desc':desc,'icon':cItem['icon']})
					
					
					
					
					
			


	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		if mode=='30':
			self.showitms1(cItem)
		if mode=='31':
			self.showitms2(cItem)		
		return True
