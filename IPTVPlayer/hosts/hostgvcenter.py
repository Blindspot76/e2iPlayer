# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import byteify, printExc
###################################################
# FOREIGN import
###################################################
import re
try:    import json
except: import simplejson as json
####################################################
# E2 GUI COMMPONENTS
####################################################

####################################################
# Config options for HOST
####################################################

####################################################
#
####################################################
HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0', 'Accept-Language': 'en-US,en;q=0.8'}

###############################################################################
# gvcenter LINKS
###############################################################################
base_link = 'http://www.gearscenter.com'
search_link2 = '/cartoon_control/gapi-202/?param_10=AIzaSyBsxsynyeeRczZJbxE8tZjnWl_3ALYmODs&param_7=2.0.2&param_8=com.appcenter.sharecartoon&os=android&versionCode=202&op_select=search_catalog&q='
source_link = '/cartoon_control/gapi-202/?param_10=AIzaSyBsxsynyeeRczZJbxE8tZjnWl_3ALYmODs&param_7=2.0.2&param_8=com.appcenter.sharecartoon&os=android&versionCode=202&op_select=films&param_15=0&id_select='
search_link = 'http://gearscenter.com/cartoon_control/gapi-ios/index.php?op_select=catalog&os=ios&param_10=AIzaSyBsxsynyeeRczZJbxE8tZjnWl_3ALYmODs&param_7=1.0.0&param_8=com.appmovies.gears&type_film=Movie'


def GetConfigList():
    optionList = []
    return optionList


def gettytul():
    return 'Gvcenter'


class Video(CBaseHostClass):
    SERVICE_MENU_TABLE = {
        1: "Alfabetycznie",
    }

    def __init__(self):
        CBaseHostClass.__init__(self)

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'category': val, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = {'name': 'abc-menu', 'category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)

###############################################################################
# GVCENTER
###############################################################################
    def gvcenter_list(self, category):
        sts, data = self.cm.getPage(search_link, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['categories']
            for x in range(len(data)):
                item = data[x]
                catalog_name = item['catalog_name']
                if catalog_name[0] == category:
                    catalog_name =catalog_name
                    catalog_id = item['catalog_id']
                    try:
                        catalog_icon = item['catalog_icon']
                    except:
                        catalog_icon = ''
                    params = {'name': 'gvcenter_list_names','title':catalog_name , 'page':catalog_id, 'icon': catalog_icon, 'plot': ''}
                    self.addDir(params)
        except:
            printExc()  # wypisz co poszło nie tak

    def gvcenter_list_names(self, url):
        sts, data = self.cm.getPage(base_link + source_link + url, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['films']
            for x in range(len(data)):
                item = data[x]
                film_name = item['film_name']
                film_link = item['film_link']
                try:
                    film_icon = item['film_icon']
                except:
                    film_icon = ''
                plot = ''
                params = {'name': 'gvcenter_quality','title': film_name, 'page': film_link, 'icon': film_icon, 'plot': plot}
                self.addDir(params)
        except:
            printExc()  # wypisz co poszło nie tak

    def gvcenter_quality(self, url, film_name):
        print 'ssssssssssss', film_name
        match = re.compile('https:(.+?)#(.+?)#').findall(url)
        if match:
            for item in match:
                url = 'https:' + item[0]
                title = film_name + " " + item[1]
                params = {'name': 'getVideoUrl','title': title, 'page': url, 'icon': '', 'plot': ''}
                self.addVideo(params)

###############################################################################
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG("handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)))
                return
            if -1 == index:
                # use default value
                self.currItem = {"name": None}
                printDBG("handleService for first self.category")
            else:
                self.currItem = self.currList[index]
        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        page = self.currItem.get("page", '')
        title = self.currItem.get("title", '')
        printDBG( "handleService: |||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []
        if str(page) == 'None' or page == '':
            page = '0'

###############################################################################
    #MAIN MENU
        if name is None:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            self.gvcenter_list(category)
        elif name == 'gvcenter_list_names':
            self.gvcenter_list_names(page)
        elif name == 'gvcenter_list':
            self.gvcenter_list(page)
        elif name == 'gvcenter_quality':
            self.gvcenter_quality(page, title)
###############################################################################


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Video(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value=[GetLogoDir('gvcenter.png')])

    def getLinksForVideo(self, Index=0, selItem=None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG("ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index))
            return RetHost(RetHost.ERROR, value=[])
        if self.host.currList[Index]["type"] != 'video':
            printDBG("ERROR getLinksForVideo - current item has wrong type")
            return RetHost(RetHost.ERROR, value=[])
        retlist = []
        urlList = self.host.currList[Index]["page"]
        need_resolve = 0
        retlist.append(CUrlItem("video", urlList, need_resolve))
        return RetHost(RetHost.OK, value=retlist)

    def getResolvedURL(self, url):
#        if url != None and url != '':
        if url is not None and url is not '':
            ret = self.host.up.getVideoLink(url)
            list = []
            if ret:
                list.append(ret)
            return RetHost(RetHost.OK, value=list)
        return RetHost(RetHost.NOT_IMPLEMENTED, value=[])

    def convertList(self, cList):
        hostList = []
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))
            title = cItem.get('title', '')
            description = cItem.get('plot', '')
            icon = cItem.get('icon', '')
            hostItem = CDisplayListItem(name=title,
                                        description=description,
                                        type=type,
                                        urlItems=hostLinks,
                                        urlSeparateRequest=1,
                                        iconimage=icon)
            hostList.append(hostItem)
        return hostList
    # end convertList


