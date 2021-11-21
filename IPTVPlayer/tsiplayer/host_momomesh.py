# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname
import re,base64
###################################################
def getinfo():
    info_={}
    info_['name']='Momomesh.Tv'
    info_['version']='1.0 03/03/2021'
    info_['dev']='RGYSoft'
    info_['cat_id']='41'
    info_['desc']='Watch Movies & TV shows'
    info_['icon']='https://momomesh.tv/wp-content/uploads/2020/07/momomesh.logo_.hd_.png'
    info_['recherche_all']='1'
    return info_
      
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'momomesh.cookie'})
        self.MAIN_URL = 'https://momomesh.tv'

    def showmenu0(self,cItem):
        hst='host2'
        img_=cItem['icon']								
        Cat_TAB = [
                    {'category':hst,'title': 'GENRES'   , 'mode':'20', 'sub_mode':0},                    
                    {'category':hst,'title': 'MOVIES'   , 'mode':'20', 'sub_mode':1},
                    {'category':hst,'title': 'TV SERIES', 'mode':'20', 'sub_mode':2},												
                    {'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
                    ]
        self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})				

    def showmenu1(self,cItem):
        self.add_menu(cItem,'<ul class="sub-menu">(.*?)</ul','<li.*?href="(.*?)".*?>(.*?)<','','30',ord=[0,1],ind_0=cItem['sub_mode'])		
    
    def showitms(self,cItem):
        desc = [('Rating','class="rating">(.*?)</div>','',''),('Quality','class="quality">(.*?)</div>','',''),('Genre','class="genres">(.*?)</div>','',''),
                ('Info','class="metadata">(.*?)</div>','\n',''),('Story','class="texto">(.*?)</div>','\n','')]
        if '?' in cItem['url']:
            next = ['class=\'arrow_pag\'.*?href="(.*?)"','30']
        else:
            next = ['rel="next.*?href="(.*?)"','30']
        self.add_menu(cItem,'','class="item .*?src="(http.*?)"(.*?)<h3>.*?href="(.*?)".*?>(.*?)<(.*?)</article>','','31',ord=[2,3,0,1,4],Desc=desc,Next=next)		

    def showelms(self,cItem):
        desc = [('Date','date\'>(.*?)</span>','','')]
        self.add_menu(cItem,'','class=\'numerando\'>(.*?)<.*?href=\'(.*?)\'.*?>(.*?)<(.*?)img src=\'(.*?)\'','','video',ord=[1,0,4,2,3],Desc=desc)		


    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
        desc = [('Type','<span class="(tvshows|movies)"','',''),('Rating','class="rating">(.*?)</span>','',''),('Year','class="year">(.*?)</span>','',''),
                ('Story','contenido">(.*?)</div>','\n','')]
        self.add_menu({'import':extra,'url':url},'','result-item">.*?href="(.*?)".*?-src="(.*?)".*?alt="(.*?)"(.*?)</article>','','31',ord=[0,2,1,3],Desc=desc)


    def get_links(self,cItem):
        #local = [('/player.html?','!!DELETE!!','1'),]
        urlTab = []
        URL = cItem['url']
        sts, data = self.getPage(URL)
        if sts:
            server_data = re.findall('<div id="(._server)".*?src="(.*?)"', data, re.S)
            for x1,link in server_data:        
                if 'exturl.php?id=' in link:
                    link = base64.b64decode(link.split('exturl.php?id=')[1]).decode("utf-8")
                titre_ = gethostname(link)
                urlTab.append({'name':titre_, 'url':link, 'need_resolve':1})
        #result = self.add_menu(cItem,'','<div id="(._server)".*?src="(.*?)"','','serv_url',ord=[1,0],local=local)	                        
        return urlTab
           
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
            