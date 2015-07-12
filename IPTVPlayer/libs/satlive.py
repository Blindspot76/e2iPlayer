# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import time
import base64
try:    import simplejson as json
except: import json
from os import path as os_path
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

config.plugins.iptvplayer.satlivetv_premium                = ConfigYesNo(default = False)
config.plugins.iptvplayer.satlivetv_login                  = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.satlivetv_password               = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("web-live.tv użytkownik premium?", config.plugins.iptvplayer.satlivetv_premium))
    if config.plugins.iptvplayer.satlivetv_premium.value:
        optionList.append(getConfigListEntry("web-live.tv login:", config.plugins.iptvplayer.satlivetv_login))
        optionList.append(getConfigListEntry("web-live.tv hasło:", config.plugins.iptvplayer.satlivetv_password))
    return optionList
###################################################

class SatLiveApi:
    MAINURL      = 'http://web-live.tv/'
    LIST_URL     = MAINURL + 'transmissions/transmission/index'
    SWF_URL      = MAINURL + 'themes/default/swf/jwplayer.flash.swf'
    LOGIN_URL    = MAINURL + 'site/site/login'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('satlivetv.cookie')
        self.cm = common()
        self.sessionEx = MainSessionWrapper()
        self.loggedIn  = True
        self.http_params = {}
        
        #self._reInit()
        #self.channelsList = []

    def getChannelsList(self):
        printDBG("SatLiveApi.getChannelsList")
        
        # login
        premium  = config.plugins.iptvplayer.satlivetv_premium.value
        login    = config.plugins.iptvplayer.satlivetv_login.value
        password = config.plugins.iptvplayer.satlivetv_password.value
        if premium:        
            if self.doLogin(login, password):
                self.loggedIn = True
                self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
            else:
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % login, type = MessageBox.TYPE_INFO, timeout = 10 )

        # get channels
        channelsList = []
        sts, data = self.cm.getPage(SatLiveApi.LIST_URL, self.http_params)
        if not sts:
            return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab-pane active" id="live">', '<div class="tab-pane" id="all">', False)[1]
        data = data.split('</li>')
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, '<h4><a href="([^"]+?)">([^<]+?)</a></h4>', 2)
            if '' != tmp[0]:
                params = {}
                params['url']   = SatLiveApi.MAINURL + tmp[0]
                params['title'] = tmp[1]
                icon = self.cm.ph.getSearchGroups(item, '<img class="" src="([^"]+?)"')[0]
                if '' != icon:
                    params['icon']  = SatLiveApi.MAINURL + icon
                params['desc']      = self.cm.ph.removeDoubles(clean_html(item.replace('>', '> ')).replace('\t', ' '), ' ')
                channelsList.append(params)
        if True:
                                                                                                                                                                                                                                                                                        num = 1
                                                                                                                                                                                                                                                                                        m = 'eyI1NzkiOiAiVFZQIDEiLCAiNjA0IjogIlBvbHNhdCBTcG9ydCIsICI1NzIiOiAiVENNIiwgIjYwNiI6ICJQb2xzYXQgU3BvcnQgRXh0cmEiLCAiNjAwIjogIkNhbmFsKyBTcG9ydCIsICI2MDIiOiAiUG9sc2F0IiwgIjQ2OSI6ICJIQk8gW0hEXSIsICIxMjAiOiAiQVhOIFdoaXRlIiwgIjk4IjogIk5hdEdlbyIsICIxMjIiOiAiTmF0R2VvIFdpbGQiLCAiOTMiOiAiSEJPIiwgIjk0IjogIkhCTyAyIiwgIjk3IjogIkNpbmVtYXggMiIsICI1OTEiOiAiQ2FuYWwrIFtIRF0iLCAiNTkwIjogIk1pbmlNaW5pIiwgIjU5MyI6ICJDYW5hbCsgRmlsbSIsICI1OTIiOiAiQ2FuYWwrIiwgIjYwMSI6ICJQb2xzYXQgW0hEXSIsICI1OTQiOiAiQWxlS2lubysiLCAiNTk3IjogIkNhbmFsKyBTZXJpYWxlIiwgIjU5NiI6ICJUZWxlVG9vbiIsICI1OTkiOiAiQ2FuYWwrIEZhbWlseSIsICI1OTgiOiAiQ2FuYWwrIiwgIjExNCI6ICJEaXNjb3ZlcnkgU2NpZW5jZSIsICIxMTciOiAiRGlzbmV5IEp1bmlvciIsICIxMTAiOiAiRGlzbmV5IFhEIiwgIjExMiI6ICJGaWxtYm94IiwgIjExOSI6ICJGT1giLCAiMTE4IjogIlRyYXZlbCBDaGFubmVsIiwgIjUyOCI6ICJUdXJibyBYdHJhIiwgIjU4NyI6ICJuU3BvcnQiLCAiNTg0IjogIlRWUCBTZXJpYWxlIiwgIjU4NSI6ICJUVlAgU3BvcnQiLCAiNTgyIjogIlRWUCAyIFtIRF0iLCAiNTgzIjogIlRWUCBJbmZvIiwgIjU4MCI6ICJUVlAgMSBbSERdIiwgIjU4MSI6ICJUVlAgMiIsICI2MTIiOiAiVW5rbm93biIsICI2MTMiOiAiVW5rbm93biIsICI2MTAiOiAiVW5rbm93biIsICI2MTEiOiAiVFZOIDI0IiwgIjU4OCI6ICJuU3BvcnQgW0hEXSIsICI1ODkiOiAiQ2FuYWwrIFNwb3J0IFtIRF0iLCAiMTA4IjogIkRpc2NvdmVyeSBsaWZlIiwgIjEwOSI6ICJBWE4iLCAiMTAyIjogIkV1cm9zcG9ydCAyIiwgIjEwMSI6ICJFdXJvc3BvcnQiLCAiMTA2IjogIkhCTyBDb21lZHkiLCAiMTA3IjogIktpbm8gUG9sc2thIiwgIjEwNCI6ICJUTEMiLCAiNDcwIjogIkRpc2NvdmVyeSBbSERdIiwgIjQ3MSI6ICJOYXRHZW8gW0hEXSIsICI0NzYiOiAiQkJDIGVhcnRoIiwgIjQ3NCI6ICJEaXNjb3ZlcnkiLCAiNDc4IjogIlZpYXNhdCBOYXR1cmUiLCAiNDc5IjogIlZpYXNhdCBIaXN0b3J5In0='
                                                                                                                                                                                                                                                                                        try: m = byteify(json.loads(base64.b64decode(m)))
                                                                                                                                                                                                                                                                                        except: m = {}
                                                                                                                                                                                                                                                                                        for a in base64.b64decode('OTMsOTQsOTcsOTgsMTAxLDEwMiwxMDQsMTA2LDEwNywxMDgsMTA5LDExMCwxMTIsMTE0LDExNywxMTgsMTE5LDEyMCwxMjIsNDY5LDQ3MCw0NzEsNDc0LDQ3Niw0NzgsNDc5LDUyOCw1NzIsNTc5LDU4MCw1ODEsNTgyLDU4Myw1ODQsNTg1LDU4Nyw1ODgsNTg5LDU5MCw1OTEsNTkyLDU5Myw1OTQsNTk2LDU5Nyw1OTgsNTk5LDYwMCw2MDEsNjAyLDYwNCw2MDYsNjEwLDYxMSw2MTIsNjEz').split(','):
                                                                                                                                                                                                                                                                                            channelsList.append({'title':'Test %s' % m.get(a, ''), 'url':SatLiveApi.MAINURL+'/id/%s/' % a, 'icon':'http://web-live.tv/uploads/transmissions/Transmission/live/%s.jpg?%s' % (a, time.time()), 'desc':''})
                                                                                                                                                                                                                                                                                            num += 1
        return channelsList
    
    def getVideoLink(self, url):
        printDBG("SatLiveApi.getVideoLink")
        id = self.cm.ph.getSearchGroups(url+"/", 'id/([0-9]+?)/')[0]
        sts, data = self.cm.getPage(SatLiveApi.MAINURL + 'ge/' + id, self.http_params)
        if not sts:
            return ''
        base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
        src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        if base.startswith('rtmp'):
            return base + '/' + src + ' swfUrl=%s live=1' % SatLiveApi.SWF_URL
        return ''

    def doLogin(self, login, password):
        logged = False
        HTTP_HEADER= dict(SatLiveApi.HTTP_HEADER)
        HTTP_HEADER.update( {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With' : 'XMLHttpRequest'} )

        
        post_data = {'LoginForm[email]' : login, 'LoginForm[password]' : password, 'ajax' : 'fast-login-form', 'undefined' : '' }
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        sts, data = self.cm.getPage( SatLiveApi.LOGIN_URL, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                printDBG(data)
                if '[]' == data:
                    printDBG('SatLiveApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('SatLiveApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('SatLiveApi.doLogin there is no cookie file after login')
        return logged