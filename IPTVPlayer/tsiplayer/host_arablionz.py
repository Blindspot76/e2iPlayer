# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.utils   import string_escape

import re,urllib
import base64

def getinfo():
    info_={}
    name = 'Arblionz'
    hst = tshost(name)	
    if hst=='': hst = 'https://arlionz.net'
    info_['host']= hst
    info_['name']=name
    info_['version']='1.2 13/03/2021'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='أفلام و مسلسلات عربية و اجنبية'
    info_['icon']='https://i.ibb.co/861LmCL/Sans-titre.png'
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
               
    def getPage1(self, baseUrl, addParams = {}, post_data = None):
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
        TAB = [('افلام','','10',0),('مسلسلات','','10',2),('انمي و كارتون','','10',4),('عروض اخري','','10',6)]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)

    def showmenu1(self,cItem):
        self.add_menu(cItem,'(?:ChildsCats">|enresCats">)(.*?)</ul','<li.*?href="(.*?)".*?>(.*?)</li>','','20',Titre='اقسام فرعية',ord=[0,1],ind_0=cItem['sub_mode'])		
        self.add_menu(cItem,'(?:ChildsCats">|enresCats">)(.*?)</ul','<li.*?href="(.*?)".*?>(.*?)</li>','','20',Titre='حسب النوع',ord=[0,1],ind_0=cItem['sub_mode']+1)
        
    def showitms(self,cItem):
        next = [1,'20']
        mode = [('','20','URL'),('/watch/','video','URL')]
        self.add_menu(cItem,'<div class="Setion--Title--mini(.*?)<Section--Titles','data-selector=".*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"','',mode,ord=[0,1,2],Next=next,u_titre=True,EPG=True,bypass=True)		
        self.add_menu(cItem,'','class="JsutNumber".*?href="(.*?)".*?>(.*?)</div>','','video',EPG=True,add_vid=False)		

    def SearchResult(self,str_ch,page,extra):
        elms = []
        data = ['','',[]]
        data_ = base64.b64encode('{"posts_per_page":20,"s":"'+str_ch+'","tax_query":{"relation":"AND"},"post_type":["post"]}')
        url = self.MAIN_URL+'/AjaxCenter/MorePosts/args/'+data_+'/type/posts/offset/'+str((page-1)*20)+'/curPage/https%3A%2F%2Farlionz.com%2FAjaxCenter%2FSearching%2F'+str_ch+'%2F/'        
        sts, data0 = self.getPage(url)
        if sts:
            mode = [('','20','URL'),('/watch/','video','URL')]        
            data = self.add_menu({'import':extra,'url':url},'','data-selector=".*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"',data0.replace('\\',''),mode,ord=[0,1,2],u_titre=True,EPG=True)		
        return data[2]
        
    def get_links(self,cItem): 		
        urlTab=[]
        URL=cItem['url']	
        sts, data = self.getPage(URL)
        if sts:
            Liste_els = re.findall('"watch".*?data-id="(.*?)"', data, re.S)	        
            if Liste_els:
                URL = self.MAIN_URL + '/AjaxCenter/Popovers/WatchServers/id/'+Liste_els[0]+'/'
                sts, data = self.getPage(URL)
                if sts:
                    printDBG('DDAATTAA='+data)
                    Liste_els = re.findall('data-selectserver=.*?"(.*?)".*?<em>(.*?)<', data, re.S)	        
                    for (url_,titre_) in Liste_els:   
                        URL = base64.b64decode(url_.replace('\\','')).decode("utf-8")+'|Referer='+self.MAIN_URL
                        urlTab.append({'name':titre_, 'url':URL, 'need_resolve':1})	        					
        return urlTab	
        
    def getArticle(self,cItem):
        Desc = [('Genre','class="genres">(.*?)</span>','',''),('Info','href="/series/age.*?>(.*?)</','',''),('Time','fa-clock far">(.*?)</span>','',''),('Year','fa-calendar far">(.*?)</span>','',''),('Story','description">(.*?)</div>','\n','')]
        desc = self.add_menu(cItem,'','class="fg1">(.*?)</aside','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]
