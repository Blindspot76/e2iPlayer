# -*- coding: utf-8 -*-
# 2021.07.19. 
###################################################
HOST_VERSION = "1.1"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.hosts import hosturllist as urllist
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import datetime
import urllib
###################################################
#repo.mvshrk.xyz/plugins/
def gettytul():
    return 'https://dmdamedia.hu' 

class Dmdamedia(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'dmdamedia', 'cookie':'dmdamedia.cookie'})
        self.MAIN_URL = 'https://dmdamedia.hu'
        self.DEFAULT_ICON_URL = "https://dmdamedia.eu/kepek/dmdamediahu.png"
        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        return self.cm.getPage(url, addParams, post_data)
    
    def getLinksForVideo(self, cItem):
        printDBG("Dmdamedia.getLinksForVideo")
        sts, data = self.getPage(cItem['url'])        
        if not sts:
            return
        share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="beagyazas">','" FRAMEBORDER', False) [1]
        share = share.replace('<iframe src="', '')
        if share != '':
            if 'https:' not in share:
                share = 'https:'+share
        else:
           share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="beagyazas">','" allowfullscreen', False) [1]
           share = share.replace('<iframe width="640" height="360" src="', '')
           if share != '':
               if 'https:' not in share:
                   share = 'https:'+share
           else:
              share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="beagyazas">','" scrolling=', False) [1]
              share = share.replace('<iframe src="', '')
              if share != '':
                  if 'https:' not in share:
                      share = 'https:'+share
              else:
                 share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="filmbeagyazas">','" FRAMEBORDER', False) [1]
                 share = share.replace('<iframe src="', '')
                 if share != '':
                     if 'https:' not in share:
                         share = 'https:'+share
                 else:
                    share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="filmbeagyazas">','" allowfullscreen', False) [1]
                    share = share.replace('<iframe width="640" height="360" src="', '')
                    if share != '':
                        if 'https:' not in share:
                            share = 'https:'+share
                    else:
                       share = self.cm.ph.getDataBeetwenMarkers(data,'<div class="filmbeagyazas">','" scrolling=', False) [1]
                       share = share.replace('<iframe src="', '')
                       if 'https:' not in share:
                           share = 'https:'+share
        share = " ".join(share.split())
        printDBG(share)
        share = share.replace(' ', '')
        
        printDBG("Dmdamedia.getLinksForVideo url[%s]" % share)
        videoUrls = []
        uri = urlparser.decorateParamsFromUrl(share)
        protocol = uri.meta.get('iptv_proto', '')
        
        printDBG("PROTOCOL [%s] " % protocol)
        
        urlSupport = self.up.checkHostSupport( uri )
        if 1 == urlSupport:
            retTab = self.up.getVideoLinkExt( uri )
            videoUrls.extend(retTab)
        elif 0 == urlSupport and self._uriIsValid(uri):
            if protocol == 'm3u8':
                retTab = getDirectM3U8Playlist(uri, checkExt=False, checkContent=True)
                videoUrls.extend(retTab)
            elif protocol == 'f4m':
                retTab = getF4MLinksWithMeta(uri)
                videoUrls.extend(retTab)
            elif protocol == 'mpd':
                retTab = getMPDLinksWithMeta(uri, False)
                videoUrls.extend(retTab)
            else:
                videoUrls.append({'name':'direct link', 'url':uri})
        return videoUrls
    
    def _uriIsValid(self, url):
        return '://' in url
    
    def listMainMenu(self, cItem):   
        printDBG('Dmdamedia.listMainMenu')
        MAIN_CAT_TAB = [{'category':'list_items',            'title': _('Filmek'), 'desc':'Figyelem: A Videa és Playtube megosztók pillanatnyilag nem támogatottak.'},
                        {'category':'list_items',            'title': _('Sorozatok'), 'desc':'Figyelem: A Videa és Playtube megosztók pillanatnyilag nem támogatottak.'},
                        {'category':'search',          'title': _('Keresés'), 'search_item':True},
                        {'category':'search_history',  'title': _('Keresési előzmények')}]
        self.listsTab(MAIN_CAT_TAB, cItem) 

    def listItemsF(self, cItem, name):
        printDBG('Dmdamedia.listItemsFilmek')
        approve = False
        url = 'https://dmdamedia.eu/film'
                        
        sts, data = self.getPage(url)
                        
        if not sts:
            return
        if name == "Akció":
            name = name.replace("ó", "o") 
            name = name.replace("A", "a")
        if name == "Vígjáték":
            name = name.replace("í", "i") 
            name = name.replace("á", "a") 
            name = name.replace("é", "e")
            name = name.replace("V", "v")
        if name == "Családi":
            name = name.replace("á", "a")
            name = name.replace("C", "c")			
        if name == "Animációs":
            name = name.replace("á", "a")
            name = name.replace("ó", "o")
            name = name.replace("A", "a")
        if name == "Történelmi":
            name = name.replace("ö", "o")
            name = name.replace("é", "e")
            name = name.replace("T", "t")
        if name == "Háborús":
            name = name.replace("á", "a")
            name = name.replace("ú", "u")
            name = name.replace("H", "h")
        if name == "Életrajzi":
            name = name.replace("É", "e")
        if name == "Mese":
            name = name.replace("M", "m")
        if name == "Horror":
            name = name.replace("H", "h")
        if name == "Romantikus":
            name = name.replace("R", "r")
        if name == "Krimi":
            name = name.replace("K", "k")
        if name == "Fantasy":
            name = name.replace("F", "f")
        if name == "Misztikus":
            name = name.replace("M", "m")
        if name == "Kaland":
            name = name.replace("K", "k")
        if name == "Sci-Fi":
            name = name.replace("S", "s")
            name = name.replace("-", "")
            name = name.replace("F", "f")
        if name == "Thriller":
            name = name.replace("T", "t")
        if name == "Western":
            name = name.replace("W", "w")
        if name == "Sport":
            name = name.replace("S", "s")
        movies = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="','"/></a>')
        for m in movies:
            cat = self.cm.ph.getAllItemsBeetwenMarkers(m,'<div class="sorozatok','" data-cim')
            for c in cat:
                see = c.split()
                see.pop(0)
                see.pop(0)
                see.pop()
                see[-1] = see[-1].replace('"', '')
                if len(see) > 1:
                    co = 0
                    while co != len(see):
                       if see[co] == name:
                           approve = True
                       co = co +1				
                if c == name:
				     approve = True
                else:
                   if name == "Összes":
                       approve = True
                if approve == True:
                    title = self.cm.ph.getDataBeetwenMarkers(m, '><h1>','</h1>', False) [1]
                    icon = self.cm.ph.getDataBeetwenMarkers(m, 'data-src="','" title', False) [1]
                    cleanurl = url.strip('film')
                    icon = cleanurl+icon
                    params = {'category':'explore_item','title':title, 'icon': icon , 'url': url}
                    self.addDir(params)
                approve = False
    
    def listItemsS(self, cItem, name):
        printDBG('Dmdamedia.listItemsSorozatok')
        approve = False
        url = 'https://dmdamedia.eu/'
                        
        sts, data = self.getPage(url)
                        
        if not sts:
            return
        name = name.lower()
        if "á" in name:
            name = name.replace("á", "a")
        if "é" in name:
            name = name.replace("é", "e")
        if "ö" in name:
            name = name.replace("ö", "o")
        if "ü" in name:
            name = name.replace("ü", "u")
        if "ó" in name:
            name = name.replace("ó", "o")
        if "ő" in name:
            name = name.replace("ő", "o")
        if "ű" in name:
            name = name.replace("ű", "u")
        if "ú" in name:
            name = name.replace("ú", "u")
        if "í" in name:
            name = name.replace("í", "i")
        if "-" in name:
            name = name.replace("-", "")
        if "befejezett" in name:
            name = name.replace("befejezett", "vege")
        series = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="','"/></a>')
        for m in series:
            cat = self.cm.ph.getAllItemsBeetwenMarkers(m,'<div class="sorozatok','" data-cim')
            for c in cat:
                see = c.split()
                see.pop(0)
                see.pop(0)
                see.pop()
                see[-1] = see[-1].replace('"', '')
                if len(see) > 1:
                    co = 0
                    while co != len(see):
                       if see[co] == name:
                           approve = True
                       co = co +1				
                if c == name:
                     approve = True
                else:
                   if name == "Összes":
                       approve = True
                if approve == True:
                    title = self.cm.ph.getDataBeetwenMarkers(m, '><h1>','</h1>', False) [1]
                    icon = self.cm.ph.getDataBeetwenMarkers(m, 'data-src="','" title', False) [1]
                    cleanurl = url.strip('film')
                    icon = cleanurl+icon
                    params = {'category':'explore_item','title':title, 'icon': icon , 'url': url}
                    self.addDir(params)
                approve = False
	
    def listFiltersF(self, cItem):
        printDBG('Dmdamedia.listFiltersFilmek')
        url = 'https://dmdamedia.eu/film'               
        sts, data = self.getPage(url)
                        
        if not sts:
            return
        cat = self.cm.ph.getAllItemsBeetwenMarkers(data,'<button class=','/button>')
        for c in cat:
            title = self.cm.ph.getDataBeetwenMarkers(c, '>','<', False) [1]
            icon = None
            params = {'category':'list_filters','title':title, 'icon': icon , 'url': url}
            self.addDir(params)
   
    def listFiltersS(self, cItem):
        printDBG('Dmdamedia.listFiltersSorozatok')
        url = 'https://dmdamedia.eu/'               
        sts, data = self.getPage(url)
                        
        if not sts:
            return
        cat = self.cm.ph.getAllItemsBeetwenMarkers(data,'<button class=','/button>')
        for c in cat:
            title = self.cm.ph.getDataBeetwenMarkers(c, '>','<', False) [1]
            icon = None
            params = {'category':'list_filters','title':title, 'icon': icon , 'url': url}
            self.addDir(params)
                        
    def exploreItemsF(self, cItem, title, icon):
        printDBG('Dmdamedia.exploreItems - Filmek')
        url = 'https://dmdamedia.eu/' 
        self.cim = title
        sts, data = self.getPage(url)
        if not sts:
            return
        title = title.lower()
        if "á" in title:
            title = title.replace("á", "a")
        if "é" in title:
            title = title.replace("é", "e")
        if "ö" in title:
            title = title.replace("ö", "o")
        if "ü" in title:
            title = title.replace("ü", "u")
        if "ó" in title:
            title = title.replace("ó", "o")
        if "ő" in title:
            title = title.replace("ő", "o")
        if "ű" in title:
            title = title.replace("ű", "u")
        if "ú" in title:
            title = title.replace("ú", "u")
        if "í" in title:
            title = title.replace("í", "i")
        if "." in title:
            title = title.replace(".", "")
        if "," in title:
            title = title.replace(",", "")
        if ":" in title:
            title = title.replace(":", "")
        if "- " in title:
            title = title.replace("- ", "")
        if "-" in title:
            title = title.replace("-", "_")
        if " " in title:
            title = title.replace(" ", "_")
        if "Állatfarm" in title:
            title = title.replace("Állatfarm", "allatfarm")
        if "terminator_a_halaloszto" in title:
            title = title.replace("terminator_a_halaloszto", "terminator_1")
        if "terminator_2_az_itelet_napja" in title:
            title = title.replace("_az_itelet_napja", "")
        if "terminator_3_a_gepek_lazadasa" in title:
            title = title.replace("_a_gepek_lazadasa", "")
        if "terminator_4_megvaltas" in title:
            title = title.replace("_megvaltas", "")
        if "terminator_5_genisys" in title:
            title = title.replace("_genisys", "")
        title = title + "_film"
        filmurl = url + title
        sts, data = self.getPage(filmurl)
        if not sts:
            return
        meg = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="lista">Megosztók</div>	','<div class="info">')
        mega = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="lista">Megosztók - feliratos</div>	','<div class="info">')
        for m in meg:
            utl = self.cm.ph.getAllItemsBeetwenMarkers(m,'<a class="','</a>')
            printDBG(m)
            for u in utl:
                ult = self.cm.ph.getAllItemsBeetwenMarkers(u,'" a href="','">')
                printDBG(u)
                for i in ult:
                    printDBG(i)
                    i = i.replace('" a href="', '')
                    i = i.replace('">', '')
                    title = self.cim + '(' + self.cm.ph.getDataBeetwenMarkers(data, '<div class="infotab-time">','</div>', False) [1] + ')' + " - " + i.replace('?a=', '')
                    url = filmurl + i
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'title': title,  'icon': icon, 'url': url, 'desc': desc}
                    self.addVideo(params)
        for o in mega:
            uzl = self.cm.ph.getAllItemsBeetwenMarkers(o,'<a class="','</a>')
            printDBG(o)
            for k in uzl:
                ui = self.cm.ph.getAllItemsBeetwenMarkers(k,'" a href="','">')
                printDBG(k)
                for b in ui:
                    printDBG(b)
                    b = b.replace('" a href="', '')
                    b = b.replace('">', '')
                    title = self.cim + '(' + self.cm.ph.getDataBeetwenMarkers(data, '<div class="infotab-time">','</div>', False) [1] + ')' + " - " + b.replace('?a=', '')
                    url = filmurl + b
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'title': title,  'icon': icon, 'url': url, 'desc': desc}
                    self.addVideo(params)
    
    def exploreItemsS(self, cItem, title, icon):
        printDBG('Dmdamedia.exploreItems - Sorozatok')
        url = 'https://dmdamedia.eu/' 
        sts, data = self.getPage(url)
        if not sts:
            return
        self.realtitle = title
        realurl = url
        title = title.lower()
        if "á" in title:
            title = title.replace("á", "a")
        if "é" in title:
            title = title.replace("é", "e")
        if "ö" in title:
            title = title.replace("ö", "o")
        if "ü" in title:
            title = title.replace("ü", "u")
        if "ó" in title:
            title = title.replace("ó", "o")
        if "ő" in title:
            title = title.replace("ő", "o")
        if "ű" in title:
            title = title.replace("ű", "u")
        if "ú" in title:
            title = title.replace("ú", "u")
        if "í" in title:
            title = title.replace("í", "i")
        if "," in title:
            title = title.replace(",", "")
        if "?" in title:
            title = title.replace("?", "")
        if "." in title:
            title = title.replace(".", "_")
        if ":" in title:
            title = title.replace(":", "")
        if "- " in title:
            title = title.replace("- ", "")
        if "-" in title:
            title = title.replace("-", "")
        if " " in title:
            title = title.replace(" ", "_")
        if "a_shield_ugynokei" in title:
            title = title.replace("a_shield_ugynokei", "a_shieldugynokei")
        if "a_sotetseg_kora" in title:
            title = title.replace("a_sotetseg_kora", "a_sotetsegkora")
        if "embertelenek" in title:
		    title = title.replace("embertelenek", "embertelenek_marvels")
        if "a_22es_csapdaja" in title:
            title = title.replace("a_22es_csapdaja", "22_es_csapdaja")
        if "ncis_tengereszeti_helyszinelok" in title:
		    title = title.replace("ncis_tengereszeti_helyszinelok", "ncis_-_tengereszeti_helyszinelok")
        if "Éber_szemek" in title:
		    title = title.replace("Éber_szemek", "eber_szemek")
        if "a_mentalista" in title:
		    title = title.replace("a_mentalista", "mentalista")
        if "a_mi_kis_falunk" in title:
		    title = title.replace("a_mi_kis_falunk", "mi_kis_falunk")
        sorurl = url + title
        sts, data = self.getPage(sorurl)
        if not sts:
            return
        meg = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="evadok">','</div>')
        for m in meg:
            utl = self.cm.ph.getAllItemsBeetwenMarkers(m,'<a class="linktab"','</a>')
            printDBG(m)
            for u in utl:
                ult = self.cm.ph.getAllItemsBeetwenMarkers(u,'href="','">')
                for i in ult:
                    i = i.replace('href="', '')
                    i = i.replace('">', '')
                    title = self.cm.ph.getDataBeetwenMarkers(u,'">','</a>', False) [1] + ".évad"
                    url = realurl.replace("/", "") + i
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'category':'explore_item', 'title': title,  'icon': icon, 'url': url, 'desc':desc}
                    self.addDir(params)
    
    def exploreItemsE(self, cItem, title, icon):
        printDBG('Dmdamedia.exploreItems - Epizódok')
        url = cItem['url']
        if "https:dmdamedia.eu" in url:
            url = url.replace("https:", "https://")
        sts, data = self.getPage(url)
        if not sts:
            return
        res = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="reszek">','</div>')
        for r in res:
            ep = self.cm.ph.getAllItemsBeetwenMarkers(r,'<a class="linktab','</a>')
            for e in ep:
                fin = self.cm.ph.getAllItemsBeetwenMarkers(e,'" href="','">')
                for f in fin:
                    f = f.replace('" href="', '')
                    f = f.replace('">', '')
                    title = self.cm.ph.getDataBeetwenMarkers(e,'">','</a>', False) [1] + ".rész" + " - " + self.cm.ph.getDataBeetwenMarkers(e,'title="','" href=', False) [1]
                    if "- feliratos rész" not in title:
                        title = title.replace("-", "")
                    url = "https://dmdamedia.eu" + f 
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'category':'explore_item', 'title': title,  'icon': icon, 'url': url, 'desc': desc}
                    self.addDir(params)
    
    def exploreItemsEL(self, cItem, title, icon):
        printDBG('Dmdamedia.exploreItems - EpizódLinkek')
        url = cItem['url']
        sts, data = self.getPage(url)
        normurl = url
        meg = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="lista">Megosztók</div>	','<div class="video">')
        mega = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="lista">Megosztók - feliratos</div>	','<div class="video">')
        for m in meg:
            utl = self.cm.ph.getAllItemsBeetwenMarkers(m,'<a class="','</a>')
            printDBG(m)
            for u in utl:
                ult = self.cm.ph.getAllItemsBeetwenMarkers(u,'" a href="','">')
                printDBG(u)
                for i in ult:
                    printDBG(i)
                    i = i.replace('" a href="', '')
                    i = i.replace('">', '')
                    title = self.realtitle + '(' + self.cm.ph.getDataBeetwenMarkers(data, '<div class="infotab-time">','</div>', False) [1] + ')' + " - " + i.replace('?a=', '')
                    url = normurl + i
                    printDBG(url)
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'title': title,  'icon': icon, 'url': url, 'desc':desc}
                    self.addVideo(params)
                    printDBG(params) 
        for e in mega:
            uti = self.cm.ph.getAllItemsBeetwenMarkers(e,'<a class="','</a>')
            printDBG(e)
            for k in uti:
                ukl = self.cm.ph.getAllItemsBeetwenMarkers(k,'" a href="','">')
                printDBG(k)
                for v in ukl:
                    printDBG(v)
                    v = v.replace('" a href="', '')
                    v = v.replace('">', '')
                    title = self.realtitle + '(' + self.cm.ph.getDataBeetwenMarkers(data, '<div class="infotab-time">','</div>', False) [1] + ')' + " - " + v.replace('?a=', '')
                    url = normurl + v
                    printDBG(url)
                    desc = "Tartalom:" + self.cm.ph.getDataBeetwenMarkers(data, '<div class="leiras">','</div>', False) [1]
                    params = {'title': title,  'icon': icon, 'url': url, 'desc':desc}
                    self.addVideo(params)
                    printDBG(params) 
	
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('Dmdamedia.handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        title = self.currItem.get("title", '')
        icon = self.currItem.get("icon", '')
        url = self.currItem.get("url", '')
        
        printDBG( "handleService: >> name[%s], category[%s], title[%s], icon[%s] " % (name, category, title, icon) )
        self.currList = []
        
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'list_items' and title == "Filmek":
            self.listFiltersF(self.currItem)
        elif category == 'list_items' and title == "Sorozatok":
            self.listFiltersS(self.currItem)
        elif category == 'list_filters' and "film" in url:
            self.listItemsF(self.currItem, title)
        elif category == 'list_filters' and "film" not in url:
            self.listItemsS(self.currItem, title)
        elif category == 'explore_item' and "film" in url:
            self.exploreItemsF(self.currItem, title, icon)
        elif category == 'explore_item' and "évad" in title:
            self.exploreItemsE(self.currItem, title, icon)
        elif category == 'explore_item' and "rész" in title:
            self.exploreItemsEL(self.currItem, title, icon)			
        elif category == 'explore_item' and "film" not in url:
            self.exploreItemsS(self.currItem, title, icon)
        elif category == 'search':
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)			
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
    
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Dmdamedia.listSearchResult - Filmek cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        printDBG(cItem)
        url = 'https://dmdamedia.eu/film'
        sts, data = self.getPage(url)           
        if not sts:
            return
        movies = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="','"/></a>')
        point = searchPattern.split()
        for p in point:
            printDBG(p)
            p = p.lower()
            for m in movies:
                title = self.cm.ph.getDataBeetwenMarkers(m, '><h1>','</h1>', False) [1]
                tik = title.split()				    
                for t in tik:
                    t = t.lower()
                    if p in t:
                         icon = self.cm.ph.getDataBeetwenMarkers(m, 'data-src="','" title', False) [1]
                         cleanurl = url.strip('film')
                         icon = cleanurl+icon
                         params = {'category':'explore_item','title':title, 'icon': icon , 'url': url}
                         self.addDir(params)
	    printDBG("Dmdamedia.listSearchResult - Sorozatok cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        printDBG(cItem)
        url = 'https://dmdamedia.eu/'	
        sts, data = self.getPage(url)           
        if not sts:
            return
        movies = self.cm.ph.getAllItemsBeetwenMarkers(data,'<div class="','"/></a>')
        point = searchPattern.split()
        for p in point:
            printDBG(p)
            p = p.lower()
            for m in movies:
                title = self.cm.ph.getDataBeetwenMarkers(m, '><h1>','</h1>', False) [1]
                tik = title.split()				    
                for t in tik:
                    t = t.lower()
                    if p in t:
                         icon = self.cm.ph.getDataBeetwenMarkers(m, 'data-src="','" title', False) [1]
                         params = {'category':'explore_item','title':title, 'icon': icon , 'url': url}
                         self.addDir(params)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Dmdamedia(), True, [])
    