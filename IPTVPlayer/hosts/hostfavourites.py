# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem, CFavItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, GetLogoDir, GetFavouritesDir
from Plugins.Extensions.IPTVPlayer.tools.iptvfavourites import IPTVFavourites
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
try:    import simplejson as json
except Exception: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return _('Favourites')

class Favourites(CBaseHostClass):
     
    def __init__(self):
        printDBG("Favourites.__init__")
        CBaseHostClass.__init__(self)
        self.helper = IPTVFavourites(GetFavouritesDir())
        self.host = None
        self.hostName = ''
        self.guestMode = False # main or guest
        
    def _setHost(self, hostName):
        if hostName == self.hostName: return True
        try:
            _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['IPTVHost'], -1)
            host = _temp.IPTVHost()
            if isinstance(host, IHost):
                self.hostName = hostName
                self.host = host
                return True
        except Exception: printExc()
        return False
        
    def isQuestMode(self):
        return self.guestMode
        
    def clearQuestMode(self):
        self.guestMode = False
                
    def listGroups(self, category):
        printDBG("Favourites.listGroups")
        sts = self.helper.load()
        if not sts: return
        data = self.helper.getGroups()
        self.listsTab(data, {'category':category})
        
    def listFavourites(self, cItem):
        printDBG("Favourites.listFavourites")
        sts, data = self.helper.getGroupItems(cItem['group_id'])
        if not sts: return
        
        typesMap = {CDisplayListItem.TYPE_VIDEO: self.addVideo, 
                    CDisplayListItem.TYPE_AUDIO: self.addAudio, 
                    CDisplayListItem.TYPE_PICTURE: self.addPicture, 
                    CDisplayListItem.TYPE_ARTICLE: self.addArticle,
                    CDisplayListItem.TYPE_CATEGORY: self.addDir}
        
        for idx in range(len(data)):
            item = data[idx]
            addFun = typesMap.get(item.type, None)
            params = {'name':'item', 'title':item.name, 'host':item.hostName, 'icon':item.iconimage, 'desc':item.description, 'group_id':cItem['group_id'], 'item_idx':idx}
            if None != addFun: addFun(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("Favourites.getLinksForVideo idx[%r]" % cItem)
        ret = RetHost(RetHost.ERROR, value = [])
        sts, data = self.helper.getGroupItems(cItem['group_id'])
        if not sts: return ret
        item = data[cItem['item_idx']]
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % item.resolver)
        
        if CFavItem.RESOLVER_URLLPARSER == item.resolver:
            self.host = None
            self.hostName = None
            retlist = []
            urlList = self.up.getVideoLinkExt(item.data)
            for item in urlList:
                name = self.host.cleanHtmlStr( item["name"] )
                url  = item["url"]
                retlist.append(CUrlItem(name, url, 0))
            ret = RetHost(RetHost.OK, value = retlist)
        elif CFavItem.RESOLVER_DIRECT_LINK == item.resolver:
            self.host = None
            self.hostName = None
            retlist = []
            retlist.append(CUrlItem('direct link', item.data, 0))
            ret = RetHost(RetHost.OK, value = retlist)
        else:
            if self._setHost(item.resolver):
                ret = self.host.getLinksForFavourite(item)
        return ret
        
    def getResolvedURL(self, url):
        try: return self.host.getResolvedURL(url)
        except Exception: return RetHost(RetHost.ERROR, value = [])

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Favourites.handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        self.currList = [] 

        self.guestMode = False
        if None == name:
            self.host = None
            self.hostName = None
            self.listGroups('list_favourites')
        elif 'list_favourites' == category:
            self.listFavourites(self.currItem)
        elif 'host' in self.currItem:
            sts, data = self.helper.getGroupItems(self.currItem['group_id'])
            if sts:
                item = data[self.currItem['item_idx']]
                if self._setHost(self.currItem['host']):
                    ret = self.host.setInitFavouriteItem(item)
                    if RetHost.OK == ret.status:
                        self.guestMode = True
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)
        
    def getCurrentGuestHost(self):
        return self.host

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Favourites(), False, [])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('favouriteslogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        if self.host.isQuestMode(): 
            return self.host.getCurrentGuestHost().getLinksForVideo(Index)
        else:
            listLen = len(self.host.currList)
            if listLen < Index and listLen > 0:
                printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
                return RetHost(RetHost.ERROR, value = [])
            
            if self.host.currList[Index]["type"] not in ['audio', 'video', 'picture']:
                printDBG( "ERROR getLinksForVideo - current item has wrong type" )
                return RetHost(RetHost.ERROR, value = [])
            return self.host.getLinksForVideo(self.host.currList[Index])
    # end getLinksForVideo
        
    def getResolvedURL(self, url):
        if self.host.isQuestMode(): 
            return self.host.getCurrentGuestHost().getResolvedURL(url)
        else:
            return self.host.getResolvedURL(url)
    
    def convertList(self, cList):
        hostList = []
        searchTypesOptions = []
        
        for cItem in cList:
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if 'category' == cItem['type']:
                if cItem.get('search_item', False):
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
            elif 'more' == cItem['type']:
                type = CDisplayListItem.TYPE_MORE
            elif 'audio' == cItem['type']:
                type = CDisplayListItem.TYPE_AUDIO
            elif 'picture' == cItem['type']:
                type = CDisplayListItem.TYPE_PICTURE
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = [],
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList
    
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        guestIndex = Index
        ret = RetHost(RetHost.ERROR, value = [])
        if not self.host.isQuestMode(): 
            ret = CHostBase.getListForItem(self, Index, refresh)
            guestIndex = 0
        if self.host.isQuestMode(): 
            ret = self.host.getCurrentGuestHost().getListForItem(guestIndex, refresh)
            for idx in range(len(ret.value)):
                ret.value[idx].isGoodForFavourites = False
        return ret

    def getPrevList(self, refresh = 0):
        ret = RetHost(RetHost.ERROR, value = [])
        if not self.host.isQuestMode() or len(self.host.getCurrentGuestHost().listOfprevList) <= 1:
            if self.host.isQuestMode(): self.host.clearQuestMode()
            ret = CHostBase.getPrevList(self, refresh)
        else:
            ret = self.host.getCurrentGuestHost().getPrevList(refresh)
            for idx in range(len(ret.value)):
                ret.value[idx].isGoodForFavourites = False
        return ret

    def getCurrentList(self, refresh = 0):
        ret = RetHost(RetHost.ERROR, value = [])
        if not self.host.isQuestMode(): 
            ret = CHostBase.getCurrentList(self, refresh)
        if self.host.isQuestMode(): 
            ret = self.host.getCurrentGuestHost().getCurrentList(refresh)
            for idx in range(len(ret.value)):
                ret.value[idx].isGoodForFavourites = False
        return ret
        
    def getMoreForItem(self, Index = 0):
        ret = RetHost(RetHost.ERROR, value = [])
        if not self.host.isQuestMode(): 
            ret = CHostBase.getMoreForItem(self, Index)
        if self.host.isQuestMode(): 
            ret = self.host.getCurrentGuestHost().getMoreForItem(Index)
            for idx in range(len(ret.value)):
                ret.value[idx].isGoodForFavourites = False
        return ret
