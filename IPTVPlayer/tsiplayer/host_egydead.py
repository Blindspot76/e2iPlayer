# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost

import re
import base64,urllib

def getinfo():
	info_={}
	name = 'EgyDead.live'
	hst = tshost(name)	
	if hst=='': hst = 'https://egydead.live'
	info_['host']= hst
	info_['name']=name
	info_['version']='1.0.01 23/10/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
	info_['icon']='https://i.ibb.co/yNNqyth/i6yz8Xs.png'
	info_['recherche_all']='1'
	#info_['update']='Fix Links Extract'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{})
		self.MAIN_URL = getinfo()['host']
		
	def showmenu(self,cItem):
		self.add_menu(cItem,'<div class="mainMenu">(.*?)</div>','(href="#">|<a>)(.*?)<.*?<ul class(.*?)</ul>','','data_out0:10',ord=[1,2],search=True,del_=['اغاني'])	

	def showmenu1(self,cItem):
		self.add_menu(cItem,'','<li.*?href="(.*?)".*?>(.*?)<',cItem.get('data_out',''),'20',del_=['برامج','العاب'])

	def showitms(self,cItem):
		desc = [('Episode','number_episode">(.*?)</span>','',''),('Info','class="label">(.*?)</span>','','')]
		next = ['class="next page-numbers".*?href="(.*?)"','20']	
		self.add_menu(cItem,'(?:class="salery-list">|class="episodes-list">|class="seasons-list">|class="cat-page">).*?class="TitleMaster">(.*?)(?:<div class="cat-page">|class="pagination">|<em>ذات صله</em>|class="TitleMaster">)','class="movieItem">.*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"(.*?)</li>','',[('','video',''),('/assembly/','20','URL'),('/season/','20','URL'),('/serie/','20','URL')],ord=[0,1,2,3],Desc=desc,Next=next,u_titre=True,EPG=True,pat3='<li.*?href="(.*?)".*?title="(.*?)"')

	def get_links(self,cItem): 		
		local = [('youdbox.','Youdbox','0'),('youtube.','TRAILER Youtube','0'),]
		result0 = self.add_menu(cItem,'','(trailerPopup)">.*?src="(.*?)"','','serv',local=local,ord=[1,0])						
		result1 = self.add_menu(cItem,'<ul class="serversList(.*?)</ul>','<li.*?data-link="(.*?)".*?>(.*?)</li>','','serv',local=local,LINK=cItem['url']+'?View=1')
		return result0[1]+result1[1]	
			
	def SearchResult(self,str_ch,page,extra):
		url = self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		desc = [('Episode','number_episode">(.*?)</span>','',''),('Info','class="label">(.*?)</span>','','')]
		self.add_menu({'import':extra,'url':url},'','class="movieItem">.*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"(.*?)</li>','',[('','video',''),('/assembly/','20','URL'),('/season/','20','URL'),('/serie/','20','URL')],ord=[0,1,2,3],Desc=desc,EPG=True)

	def getArticle(self,cItem):
		Desc = [('Genre','<span>النوع : </span>(.*?)</li>','',''),('Quality','<span>الجوده : </span>(.*?)</li>','',''),('Country','<span>البلد : </span>(.*?)</li>','',''),('Year','<span>السنه : </span>(.*?)</li>','',''),('Date','<span>تاريخ الاصدار : </span>(.*?)</li>','',''),('Duration','<span>مده العرض : </span>(.*?)</li>','',''),('Story','<span>القصه</span>(.*?)</div>','\n','')]
		desc = ''
		desc = self.add_menu(cItem,'','extra-content">(.*?)<form','','desc',Desc=Desc)	
		if desc =='': desc = cItem.get('desc','')
		return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]

		
