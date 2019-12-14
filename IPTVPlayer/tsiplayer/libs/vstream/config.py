#-*- coding: utf-8 -*-
import os
import sys

from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetCookieDir

#---------------------------------------------------------
#          Cookies gestion  From vStream Thx
#  Repo:https://github.com/Kodi-vStream/venom-xbmc-addons
#---------------------------------------------------------

class GestionCookie():
    PathCache = GetCookieDir('')

    def DeleteCookie(self,Domain):
        Name = ''.join([self.PathCache, "cookie_%s.txt"]) % (Domain)
        try:
            os.remove(Name)
        except:
            pass

    def SaveCookie(self,Domain,data):
        Name = ''.join([self.PathCache, "cookie_%s.txt"]) % (Domain)
        f = open(Name, 'w')
        f.write(data)
        f.close()

    def Readcookie(self,Domain):
        Name = ''.join([self.PathCache, "cookie_%s.txt"]) % (Domain)

        try:
            f = open(Name,'r')
            data = f.read()
            f.close()
        except:
            return ''

        return data

    def AddCookies(self):
        cookies = self.Readcookie(self.__sHosterIdentifier)
        return 'Cookie=' + cookies
