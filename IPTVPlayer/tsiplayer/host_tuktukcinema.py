# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass
import re

def getinfo():
    info_={}
    info_['name'] = 'TukTukCinema'
    info_['version']='0.1'
    info_['dev']='Tunisia-Sat'
    info_['cat_id']='21'
    info_['desc']='هنا معلومات عن الموقع'
    info_['icon']='https://tuktukcinema.net/wp-content/uploads/2021/01/lela.png'
    return info_
   
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{})
        self.MAIN_URL      = 'https://tuktukcinema.net'
              
    def showmenu(self,cItem):
        printDBG('Start menu0')
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'Film'   ,'icon':cItem['icon'],'mode':'10','url':self.MAIN_URL+'/category/movies-10/'})
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'Anime'  ,'icon':cItem['icon'],'mode':'10','url':self.MAIN_URL+'/category/انمي/'})
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'TV'     ,'icon':cItem['icon'],'mode':'10','url':self.MAIN_URL+'/category/series/?sercat=all'})	
        self.addDir({'import':cItem['import'],'category' : 'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})	


    def showgenre(self,cItem):
        printDBG('Start menu Genre')
        URL = cItem.get('url','')
        sts, data = self.getPage(URL)
        if sts:
            data = re.findall('(?:class="genresCat">|class="sercat">)(.*?)</ul>', data, re.S)
            if data:
                Liste_els = re.findall('<li.*?href="(.*?)".*?>(.*?)</li>', data[0], re.S)
                for (url,titre) in Liste_els:
                    titre = self.cleanHtmlStr(titre) 
                    self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'icon':'','mode':'20','url':url})

    def showitms(self,cItem):
        printDBG('Start menu showitms')
        page = cItem.get('page',1)
        URL = cItem.get('url','')+'&offset='+str(page)
        sts, data = self.getPage(URL)
        if sts:
            Liste_els = re.findall('class="MovieItem">.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)".*?cats">(.*?)</ul>', data, re.S)
            for (titre,url,image,categorie) in Liste_els:
                desc0,titre = self.uniform_titre(titre)
                desc = desc0 + 'Cat: ' + self.cleanHtmlStr(categorie) 
                self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'icon':image,'desc':desc,'mode':'21','url':url,'EPG':True,'good_for_fav':True,'hst':'tshost'})
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'Next Page','icon':cItem['icon'],'desc':'','mode':'20','url':cItem['url'],'page':page+1})


    def showelms(self,cItem):
        printDBG('Start menu showelms')
        URL = cItem.get('url','')
        sts, data = self.getPage(URL)
        if sts:
            Liste_els = re.findall('class="watchAndDownlaod".*?href="(.*?)"', data, re.S)
            if Liste_els:
                url = Liste_els[0]
                self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title'],'url':url ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'tshost'})
            else:
                url_post = self.MAIN_URL + '/wp-admin/admin-ajax.php'
                id_ = slug_ = parent_ = ''
                # search for id
                id_tab = re.findall('data-id="(.*?)"', data, re.S)                
                if id_tab:
                    id_ = id_tab[0]
                # search for slug
                slug_tab = re.findall('data-slug="(.*?)"', data, re.S)                
                if slug_tab:
                    slug_ = slug_tab[0]                        
                # search for parent
                parent_tab = re.findall('data-parent="(.*?)"', data, re.S)                
                if parent_tab:
                    parent_ = parent_tab[0]                  
                post_data = {'action':'getTabsInsSeries','id':id_,'slug':slug_,'parent':parent_}
                sts, data = self.getPage(url_post,post_data=post_data)
                if sts:
                    data = re.findall('class="tabContents">(.*?)</section>', data, re.S)                     
                    if data:
                        Liste_els = re.findall('<a href="(.*?)".*?<h2>(.*?)</h2>', data[0], re.S) 
                        for (url,titre) in Liste_els:
                            self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'icon':cItem['icon'],'desc':cItem['desc'],'mode':'21','url':url})                            
       
    def get_links(self,cItem): 	
        urlTab = []	
        URL=cItem['url']
        sts, data = self.getPage(URL)
        if sts:
            Liste_els = re.findall('class="serverItem.*?server="(.*?)".*?>(.*?)</li>', data, re.S)
            for (url,titre) in Liste_els:
                titre = self.cleanHtmlStr(titre)
                url = url+'|Referer='+URL
                urlTab.append({'name':titre, 'url':url, 'need_resolve':1})	
        return urlTab


    def getArticle(self,cItem):
        Desc = [('Genre','catssection">(.*?)</div','',''),('Story','<p>(.*?)</p>','\n','')]
        desc = self.add_menu(cItem,'','class="story">(.*?)</article>','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]


    def SearchResult(self,str_ch,page,extra):
        URL=self.MAIN_URL+'/search/'+str_ch+'/page/'+str(page)
        sts, data = self.getPage(URL)
        if sts:
            Liste_els = re.findall('class="MovieItem">.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)".*?cats">(.*?)</ul>', data, re.S)
            for (titre,url,image,categorie) in Liste_els:
                desc = 'Cat: ' + self.cleanHtmlStr(categorie) 
                self.addDir({'import':extra,'category' : 'host2','title':titre,'icon':image,'desc':desc,'mode':'21','url':url,'hst':'tshost' })
       
    def start(self,cItem):
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu(cItem)
        if mode=='10':
            self.showgenre(cItem)            
        if mode=='20':
            self.showitms(cItem)   
        if mode=='21':
            self.showelms(cItem)              