# -*- coding: utf-8 -*-
###################################################
# 2019-04-10 Celeburdi
###################################################
HOST_VERSION = "1.1"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
#from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
###################################################
from xml.sax import saxutils
import re
import os
#import datetime
from datetime import datetime, timedelta
import time
import zlib
import cookielib
import urllib
import base64
from Components.config import config, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

def gettytul():
    return 'Sony Player HU'

def _gh(url):
    if not url: return ""
    return "https://celeburdi.github.io/static/icons/"+url

class SonyPlayerHU(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {"history":"sonyplayer.hu", "cookie":"sonyplayerhu.cookie"})

        self.DEFAULT_ICON_URL = _gh("sonypictures.jpg")
        self.HEADER = self.cm.getDefaultHeader()
        self.MAIN_URL = "https://hu.axn.com/"

        self.loggedIn = False

        self.defaultParams = {"header":self.HEADER}

        self.sites = ["axn","viasat","sonymax","sonymovie"]
        self.siteDefs = [ {"title": "AXN HU Player", "icon": _gh("axnplayer.jpg"), "base": "https://hu.axn.com", "all": "/axn-player/minden-video" },
                          {"title": "Viasat HU Play", "icon": _gh("viasatplay.jpg"), "base": "https://www.viasat3.hu", "all": "/viasat-play/minden-video" },
                          {"title": "Sony MAX HU "+_("Videos"), "icon": _gh("sonymax-wapadedrud.jpg"), "base": "https://www.sonymax.hu", "all": "/videok/all" },
                          {"title": "Sony Movie Channel HU "+ _("Videos"), "icon": _gh("sonymoviechannel-wapadedrud.jpg"), "base": "https://www.sonymoviechannel.hu", "all": "/videok/minden" }
                        ]

 
    def getFullIconUrl(self, url):
        if not url: return self.DEFAULT_ICON_URL
        return url

    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        baseUrl = self.cm.iriToUri(url)
        return self.cm.getPage(baseUrl, addParams, post_data)
    
    def listMainMenu(self, cItem):
        printDBG("SonyPlayerHU.listMainMenu")
        for i,site in enumerate(self.sites):
            self.addDir({"category":"list_videotypes", "title": self.siteDefs[i]["title"], "icon": self.siteDefs[i]["icon"], "site": site } )

    def listVideotypes(self, cItem):
        printDBG("SonyPlayerHU.listVideotypes")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)

        if len(sitedef["jumps"]) > 0:
            params = dict(cItem)
            params.update( { "category":"list_jumps", "title": _("Broadcasts") } )
            self.addDir(params)

        for i in sitedef["videotypes"]:
            name = i["name"]
            value = i["value"]
            if value == "All":
                name = _("All")
            params = dict(cItem)
            params.update( { "category":"list_genres", "title": name, "url": value } )
            self.addDir(params)


    def listGenres(self, cItem):
        printDBG("SonyPlayerHU.listGenres")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)
        url = cItem["url"]
        for i in sitedef["genres"]:
            name = i["name"]
            value = i["value"]
            if value == "All":
                name = _("All")
            params = dict(cItem)
            params.update( { "category":"list_sortbys", "title": name, "url": url+"{}"+value} )
            self.addDir(params)

    def listSortbys(self, cItem):
        printDBG("SonyPlayerHU.listSortbys")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)
        url = cItem["url"]
        for i in sitedef["sortbys"]:
            name = i["name"]
            value = i["value"]
            params = dict(cItem)
            params.update( { "category":"list_filtered", "title": name, "url": url+"{}"+value} )
            self.addDir(params)

    def listFiltered(self, cItem):
        printDBG("SonyPlayerHU.listFiltered")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)
        page=cItem.get("page",0)
        cItem.pop("page",None)

        url = sitedef["base"]+"/views/ajax?field_video_type_tid_selective="+cItem["url"].format("&field_genre_tid_selective=","&sort_by=")+"&view_name=videos&view_display_id=all_3up&view_path=videos%2Fall&pager_element=0&page="+str(page)

        try:
            sts, data = self.cm.getPage(url, self.defaultParams)
            if not sts: raise Exception("Can't get "+url+" page")
            data = json_loads(data)
             
            episodes=data[0]["settings"].get("spti_gigya_share")
            if not episodes: return


            i=next((i for i in data if i["command"] == "insert" and i["selector"] == ".view-dom-id-"), None)

            if i: data = i["data"]
            else: data = ""

            if 'class="pager pager-load-more"' in data:
                page = page + 1
            else: page = 0

            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="card video"', '</li>', False)

            for i,episode in enumerate(episodes):
                title = episode["title"]
                url = episode["url"]
                icon = episode["image"]
                desc = ""
                if i < len(data):
                    desc = self.cm.ph.getDataBeetwenMarkers(data[i], '<div class="type">', "</div>", False)[1]
                    tmp = self.cm.ph.getDataBeetwenMarkers(data[i], '<div class="meta">', "</div>", False)[1]
                    tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<span>', '</span>', False)
                    if len(tmp) >= 2 and tmp[0] == "Hossz":
                        if desc: desc = desc + " "
                    desc = desc + tmp[1]
                    tmp = self.cm.ph.getDataBeetwenMarkers(data[i], '<div class="more">', "/a>", False)[1]                
                    tmp = clean_html(self.cm.ph.getDataBeetwenMarkers(tmp, ">", "<", False)[1])
                    if desc and tmp: desc = desc + '\n'
                    desc = desc + tmp
                
                params=dict(cItem)
                params.update( {"title": title, "icon": icon, "url": url, "desc": desc } )
                self.addVideo(params)

            if page > 0 and len(self.currList) > 0:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':page})
                self.addDir(params)


        except Exception(): printExc()
 
    def listJumps(self, cItem):
        printDBG("SonyPlayerHU.listJumps")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)

        for i in sitedef["jumps"]:
            name = i["name"]
            value = i["value"]
            params = dict(cItem)
            params.update( { "category":"list_episodes", "title": name, "url": value } )
            self.addDir(params)

    def listEpisodes(self, cItem):
        printDBG("SonyPlayerHU.listEpisodes")
        site=cItem["site"]
        if not site in self.sites: return
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)
        page=cItem.get("page",0)
        cItem.pop("page",None)
        url = cItem["url"]
        try:
            sts, data = self.cm.getPage(sitedef["base"]+url+"?page="+str(page), self.defaultParams)
            if not sts: raise Exception("Can't get "+url+" page")
            if 'class="pager pager-load-more"' in data:
                page = page + 1
            else: page = 0
             
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="card video"', '</li>', False)
            for i in data:
                tmp = self.cm.ph.getDataBeetwenMarkers(i, "<div class=promo>", "</a>", False)[1]                
                url = sitedef["base"]+self.cm.ph.getDataBeetwenMarkers(tmp, 'href="', '">', False)[1]
                icon = self.cm.ph.getDataBeetwenMarkers(tmp, 'src="', '?', False)[1]
                title = clean_html(self.cm.ph.getDataBeetwenMarkers(tmp, "class=title>", "<", False)[1])

                desc = self.cm.ph.getDataBeetwenMarkers(i, '<div class=type>', "</div>", False)[1]
                tmp = self.cm.ph.getDataBeetwenMarkers(i, '<div class=meta>', "</div>", False)[1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<span>', '</span>', False)
                if len(tmp) >= 2 and tmp[0] == "Hossz":
                    if desc: desc = desc + " "
                    desc = desc + tmp[1]

                tmp = self.cm.ph.getDataBeetwenMarkers(i, "<div class=more>", "/a>", False)[1]                
                tmp = clean_html(self.cm.ph.getDataBeetwenMarkers(tmp, ">", "<", False)[1])
                if desc and tmp: desc = desc + '\n'
                desc = desc + tmp
                params = dict(cItem)
                params.update( {"title": title, "url": url, "icon": icon, "desc": desc } )
                self.addVideo(params)

            if page > 0 and len(self.currList) > 0:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':page})
                self.addDir(params)
        except Exception(): printExc()

    def getLinksForVideo(self, cItem):
        url = cItem['url']
        printDBG("SonyPlayerHU.getLinksForVideo url[%s]" % url)

        site=cItem["site"]
        if not site in self.sites: return []
        sitedef=self.siteDefs[self.sites.index(site)]
        self.tryTologin(sitedef)

        sts, data = self.cm.getPage( url, self.defaultParams)
        if not sts: return []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', False)
        url = ""
        for i in data:
            tmp = self.cm.ph.getDataBeetwenMarkers(i, 'src="', '"', False)[1]
            if "player.theplatform.com" in tmp:
                url = tmp
                break
        if not url: return []

        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return []
        url = self.cm.ph.getDataBeetwenMarkers( data, '<link rel="alternate" href="', '"', False)[1]
        if not url: return []

        if site == "sonymax":
            url=url.replace("form=rss","form=json")
            url=url + "&types=none&httpError=false&fields=content&params=auto%3Dtrue%26mbr%3Dtrue%26assetTypes%3DAdaptive%26player%3DSPT%2520Player%2520-%2520Universal&validFeed=false&omitInvalidFields=true&byContent=byFormat%3Dm3u%257Cmpeg4&range=1-10&count=true&fileFields=bitrate%2Cduration%2Cformat%2Curl"

            sts, data = self.cm.getPage(url, self.defaultParams)
            if not sts: return []
            try:
                data = json_loads(data)
                data = data["entries"][0]["media$content"]
                maxbitrate = 0
                url = ""
                for i in data:
                    bitrate = float(i["plfile$bitrate"])
                    tmp = i["plfile$url"]                
                    if bitrate > maxbitrate:
                        maxbitrate = bitrate
                        url = tmp
            except Exception:
                printExc()
                return []
        else:
            sts, data = self.cm.getPage(url, self.defaultParams)
            if not sts: return []

            data = self.cm.ph.getAllItemsBeetwenMarkers( data, '<media:content', '</media:content>', False)

            maxbitrate = 0;
            url = ""
            for i in data:
                tmp = self.cm.ph.getDataBeetwenMarkers(i,'url="','"', False)[1]
                bitrate = float(self.cm.ph.getDataBeetwenMarkers(i,'bitrate="','"', False)[1])
                if bitrate > maxbitrate:
                    maxbitrate = bitrate
                    url = tmp.replace("&amp;","&")
                    
            if not url: return []
            sts, tmp = self.cm.getPage(url, self.defaultParams) 
            if not sts: return []
            url = self.cm.ph.getDataBeetwenMarkers(tmp,'<video src="','"', False)[1]

        if not url: return []

        url = strwithmeta(url)
        url.meta["iptv_proto"] = "m3u8"
        #url.meta["User-Agent"] = self.HEADER["User-Agent"]

        return [{"name": "direct link", "url": url}]

    def getFavouriteData(self, cItem):
        printDBG('SonyPlayerHU.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'icon':cItem['icon']}
        return json_dumps(params)

    def getArticleContent(self, cItem):
        printDBG("SonyPlayerHU.getArticleContent [%s]" % cItem)
        if cItem["type"] == "video":
            if "epg" in cItem: self.getEpg(self.tvEpgs[cItem["epg"]])
        elif cItem["type"] == "audio":
            if "epg" in cItem: self.getEpg(self.radioEpgs[cItem["epg"]])
        retTab = {'title':cItem['title'], 'text': cItem['desc'], 'images':[{'title':'', 'url':self.getFullIconUrl(cItem.get('icon'))}]}
        return [retTab]


    def tryTologin(self,sitedef):

        def _getOptions(options):

            retList = []
            data = self.cm.ph.getAllItemsBeetwenMarkers(options, '<option', '/option>', False)
            for i in data:
                name = self.cm.ph.getDataBeetwenMarkers(i, ">", "<", False)[1]
                value = self.cm.ph.getDataBeetwenMarkers(i, "value=", ">", False)[1]
                value = value.replace(" selected","")
                value = value.replace('"','')
                if not value: continue
                if next((x for x in retList if x["name"] == name and x["value"] == value), None): continue  
                retList.append( {"name": name, "value": value } )
            return retList
            
        printDBG("SonyPlayerHU.tryTologin")
        if sitedef.get("videotypes"): return
        sitedef.update({"videotypes": [], "genres": [], "sortbys": [], "jumps": [] }) 
        try:
            url = sitedef["base"]+sitedef["all"]
            sts, data = self.cm.getPage( url, self.defaultParams)
            if not sts: raise Exception("Can't get "+url+" page")
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<select', '</select>', False)
            for i in data:
                if "id=edit-field-video-type-tid-selective" in i:
                    sitedef["videotypes"] = _getOptions(i)
                elif "id=edit-field-genre-tid-selective" in i:
                    sitedef["genres"] = _getOptions(i)
                elif "id=edit-sort-by" in i:
                    sitedef["sortbys"] = _getOptions(i)
                elif "id=edit-jump" in i:
                    sitedef["jumps"] = _getOptions(i)
        except Exception: printExc()
   

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == "list_videotypes":
            self.listVideotypes(self.currItem) 
        elif category == "list_genres":
            self.listGenres(self.currItem)
        elif category == "list_sortbys":
            self.listSortbys(self.currItem)
        elif category == "list_filtered":
            self.listFiltered(self.currItem)
        elif category == "list_jumps":
            self.listJumps(self.currItem)
        elif category == "list_episodes":
            self.listEpisodes(self.currItem)
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SonyPlayerHU(), True, [])

    def withArticleContent(self, cItem):
        return cItem['type'] == 'video' or cItem['type'] == "audio"

