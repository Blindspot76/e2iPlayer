# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

def getinfo():
    info_={}
    info_['name']='Mycima.Tv'
    info_['version']='1.2 31/10/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='201'
    info_['desc']='افلام و مسلسلات كرتون'
    info_['icon']='https://i.ibb.co/18mqGhF/my-cima.png'
    info_['recherche_all']='0'
    return info_

class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'mycima.cookie'})
        self.MAIN_URL   = 'https://mycima.video'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.011'
        self.HEADER     = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
                
    def showmenu(self,cItem):
        TAB = [('أفلام','','10',0),('مسلسلات','','10',1),('أنمي','','10',2),('المزيد','','10',3),('نوع العرض','','11',0)]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)
    
    def showmenu1(self,cItem):
        self.add_menu(cItem,'<ul class="sub-menu">(.*?)</ul','<li.*?href="(.*?)".*?>(.*?)</li>','','20',ind_0=cItem.get('sub_mode',0))		

    def showmenu2(self,cItem):
        self.add_menu(cItem,'<list--filterbox>(.*?)</list--filterbox>','data-term="(.*?)">(.*?)</item>','','20',pref_=self.MAIN_URL + '/AjaxCenter/Filtering/genre/')	
        
    def showitms(self,cItem):
        if '/Filtering/genre/' in cItem['url']: 
            URL=''
            page = cItem.get('page',1)
            if page!=1: URL = cItem['url'] + '/offset/'+str((page-1)*30)+'/'
            self.add_menu(cItem,'','GridItem.*?href=."(.*?)".*?title=."(.*?)".*?url.(.*?)\)','','21',Next=[2,'20'],ord=[0,1,2],u_titre=True,EPG=True,LINK=URL)               
        else:
            Next = ['class="next page.*?href="(.*?)"','20']
            self.add_menu(cItem,'<div class="Grid--MycimaPosts">(.*?)(?:class="pagination">|class="RightUI">)','class="GridItem".*?href="(.*?)".*?image:url\((.*?)\).*?</span>(.*?)</strong>(.*?)</ul>','','21',Next=Next,ord=[0,2,1,3],u_titre=True,EPG=True)
    
    def showelms(self,cItem):
        self.add_menu(cItem,'class="List--Seasons--Episodes">(.*?)</div>','href="(.*?)".*?>(.*?)<','','21', Titre='Seasons',EPG=True)
        self.add_menu(cItem,'Episodes--Seasons--Episodes(.*?)</singlesection','href="(.*?)".*?>(.*?)</episodeTitle>','','video', Titre='Episodes',EPG=True)

    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/search/'+str_ch+'/page/'+str(page)
        self.add_menu({'import':extra,'url':url},'<div class="Grid--MycimaPosts">(.*?)(?:class="pagination">|class="RightUI">)','class="GridItem".*?href="(.*?)".*?image:url\((.*?)\).*?</span>(.*?)</strong>(.*?)</ul>','','21',ord=[0,2,1,3],u_titre=True,EPG=True)

    def getArticle(self,cItem):
        Desc = [('Title','<span>الإسم بالعربي</span>(.*?)</li>','',''),('Country/Lang','<span>البلد و اللغة</span>(.*?)</li>','',''),('Time','<span>المدة</span>(.*?)</li>','',''),
                ('Genre','<span>النوع</span>(.*?)</li>','',''),('Quality','<span>الجودة</span>(.*?)</li>','',''),('Time','<span>مدة الحلقة</span>(.*?)</li>','',''),
                ('Category','<span>التصنيف</span>(.*?)</li>','',''),('Story','StoryMovieContent">(.*?)</div>','\n','')]
        desc = self.add_menu(cItem,'','','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]

    def get_links(self,cItem): 		
        local = [('mycima.','MyCima','1'),]
        result = self.add_menu(cItem,'WatchServersList">(.*?)</ul','<li.*?url="(.*?)".*?>(.*?)</li>','','serv',local=local)						
        return result[1]	

    def getVideos(self,videoUrl):
        result = self.add_menu({'url':videoUrl},'sources: \[(.*?)\]','format:.*?["\'](.*?)["\'].*?src:.*?["\'](.*?)["\']','','link4',ord=[1,0])	
        if result[1] ==[]: result = self.add_menu({'url':videoUrl},'','source.*?(src)="(.*?)"',result[0],'link4',ord=[1,0])	
        return result[1]	
        
