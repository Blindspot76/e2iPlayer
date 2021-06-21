# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost

import re,urllib

def getinfo():
    info_={}
    name = 'Arblionz'
    hst = tshost(name)	
    if hst=='': hst = 'https://arblionz.plus'
    info_['host']= hst
    info_['name']=name
    info_['version']='1.2 13/03/2021'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='أفلام و مسلسلات عربية و اجنبية'
    info_['icon']='https://arblionz.cam/public/img/logo.png'
    info_['recherche_all']='1'
    return info_

    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'arblionz.cookie'})
        self.MAIN_URL      = getinfo()['host']
        self.SiteName      = getinfo()['name']
        self.USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER        = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HEADER,'no_redirection':True,'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
               
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        baseUrl=self.std_url(baseUrl)
        if addParams == {}: addParams = dict(self.defaultParams)
        sts,data = self.cm.getPage(baseUrl, addParams, post_data)
        code = data.meta.get('status_code','')  
        if code == 302:
            new_url = data.meta.get('location','')
            if not new_url.startswith('http'):
                new_url = self.MAIN_URL + new_url
            new_url=self.std_url(new_url)
            sts,data = self.cm.getPage(new_url, addParams, post_data)
        elif str(data).strip() == '':
            url0       = self.MAIN_URL+'/ajax'
            post_data0 = {'action':'action_page_load'}
            addParams0 = dict(self.defaultParams)
            addParams0['header']['X-Requested-With'] = 'XMLHttpRequest'
            sts0,data0 = self.cm.getPage(url0, addParams0, post_data0)
            sts,data = self.cm.getPage(baseUrl, addParams, post_data)  
        return sts,data

    def showmenu(self,cItem):
        TAB = [('افلام','/browse','10',0),('مسلسلات','/browse','10',1),('أخري','/browse','10',2)]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)

    def showmenu1(self,cItem):
        self.add_menu(cItem,'<ul class="sub-menu">(.*?)</ul>','<li.*?href="(.*?)".*?>(.*?)</li>','','20',ord=[0,1],ind_0=cItem['sub_mode'])		

    def showitms(self,cItem):
        desc = [('Rating','class="vote">(.*?)</div>','',''),('Quality','class="Qlty".*?>(.*?)</span>','',''),('Year','class="year">(.*?)</span>','','')]
        next = ['class="page-link".*?href="(.*?)"','20']
        mode = [('','20','URL'),('/episode/','video','URL'),('/film/','video','URL'),('/wwe/','video','URL')]
        self.add_menu(cItem,'','<article.*?title">(.*?)<(.*?)src="(.*?)"(.*?)href="(.*?)"','',mode,ord=[4,0,2,1,3],Desc=desc,Next=next,u_titre=True,EPG=True)		

    def SearchResult(self,str_ch,page,extra):
        elms = []
        url = self.MAIN_URL+'/search?s='+str_ch
        desc = [('Rating','class="vote">(.*?)</div>','',''),('Quality','class="Qlty".*?>(.*?)</span>','',''),('Year','class="year">(.*?)</span>','','')]
        mode = [('','20','URL'),('/episode/','video','URL'),('/film/','video','URL'),('/wwe/','video','URL')]
        data = self.add_menu({'import':extra,'url':url},'','<article.*?title">(.*?)<(.*?)src="(.*?)"(.*?)href="(.*?)"','',mode,ord=[4,0,2,1,3],Desc=desc,u_titre=True,EPG=True,year_op=1)		
        return data[2]
        
    def get_links(self,cItem): 		
        local = [('moshahda.online','Moshahda','0'),]
        result = self.add_menu(cItem,'<section class="section player(.*?)</section>','<iframe.*?(src)="(.*?)"','','serv_url',ord=[1,0],local=local)						
        return result[1]	
        
    def getArticle(self,cItem):
        Desc = [('Genre','class="genres">(.*?)</span>','',''),('Info','href="/series/age.*?>(.*?)</','',''),('Time','fa-clock far">(.*?)</span>','',''),('Year','fa-calendar far">(.*?)</span>','',''),('Story','description">(.*?)</div>','\n','')]
        desc = self.add_menu(cItem,'','class="fg1">(.*?)</aside','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]
