# -*- coding: utf-8 -*-
#

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.components.ihost import CFavItem
###################################################

###################################################
# FOREIGN import
###################################################
import codecs
from os import path as os_path
try: import json
except: import simplejson as json

from Plugins.Extensions.IPTVPlayer.components.ihost import CFavItem
###################################################


class IPTVFavourites:
    FILE_NAME_MACRO = 'iptv_%s.fav'
    GROUPS_FILE_NAME = FILE_NAME_MACRO % 'groups' 
    def __init__(self, favDir):
        self.lastError = ''
        self.favDir = favDir
        self.groups = []
        
    def getLastError(self):
        return self.lastError
        
    def load(self, groupsOnly=False):
        ret = self._loadGroups()
        if not ret: lastError = self.lastError
        else: lastError = ''
        if ret and not groupsOnly:
            for idx in range(len(self.groups)):
                ret = self._loadItems(idx)
                if not ret: lastError += self.lastError
        if not ret: self.lastError = lastError
        return ret
        
    def save(self, groupsOnly=False):
        ret = self._saveGroups()
        if not ret: lastError = self.lastError
        else: lastError = ''
        if ret and not groupsOnly:
            for idx in range(len(self.groups)):
                ret = self._saveItems(idx)
                if not ret: lastError += self.lastError
        if not ret: self.lastError = lastError
        return ret
    
    def getGroups(self):
        return self.groups
        
    def addGroup(self, group):
        idx = self._getGroupIdx(group['group_id'])
        if -1 == idx:
            if 'items' not in group: group['items'] = []
            self.groups.append(group)
            return True
        else: 
            self.lastError = _("Group [%s] already exists") % group['group_id']
            return False

    def modifyGroup(self, group):
        idx = self._getGroupIdx(group['group_id'])
        if -1 != idx:
            group['items'] = self.groups[idx].get('items', [])
            self.groups[idx] = group
            return True
        else: return False

    def delGroup(self, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx: 
            del self.groups[idx]
            return True
        else: return False
        
    def saveGroupItems(self, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx: return self._saveItems(idx)
        else: return False
    
    def getGroupItems(self, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx: return True, self.groups[idx].get('items', [])
        return False, []
        
    def loadGroupItems(self, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx: return self._loadItems(idx)
        return False
        
    def addGroupItem(self, item, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx:
            items = self.groups[idx].get('items', [])
            exists = False
            for tmp in items: 
                if tmp.getAsDict() == item.getAsDict():
                    exists = True
                    break
            if not exists:
                items.append(item)
                self.groups[idx]['items'] = items
                return True
            else: self.lastError = _("The same item already exists in this group!")
        return False

    def delGroupItem(self, itemIdx, group_id):
        idx = self._getGroupIdx(group_id)
        if -1 != idx:
            try: del self.groups[idx]['items'][itemIdx]
            except:
                printExc()
                self.lastError = _("Item idx[%d] not found in group[%s]!") % (itemIdx, group_id)
                return False
            return True
        else: return False
        
    def _getGroupIdx(self, group_id):
        for idx in range(len(self.groups)):
            if group_id == self.groups[idx]['group_id']:
                return idx
        self.lastError = _("Group with id[%s] not found!") % group_id
        return -1
        
    def _loadItems(self, groupIdx):
        ret = True
        filePath = os_path.join(self.favDir, IPTVFavourites.FILE_NAME_MACRO % self.groups[groupIdx]['group_id'])
        if os_path.isfile(filePath):
            try:
                data = self._loadFromFile(filePath)
                printDBG(data)
                data = byteify( json.loads(data) )
                favItems = []
                for item in data:
                    favItems.append( CFavItem().setFromDict(item) )
                self.groups[groupIdx]['items'] = favItems
            except:
                printExc()
                self.lastError = _('Error reading file [%s].\n') % filePath
                ret = False
        else: self.groups[groupIdx]['items'] = []
        return ret
        
    def _loadGroups(self):
        ret = True
        filePath = os_path.join(self.favDir, IPTVFavourites.GROUPS_FILE_NAME)
        if os_path.isfile(filePath):
            try:
                data = self._loadFromFile(filePath)
                printDBG(data)
                data = byteify( json.loads(data) )
                self.groups = data
            except:
                printExc()
                self.lastError = _('Error reading file [%s].\n') % filePath
                ret = False
        else: self.groups = []
        return ret
        
    def _saveItems(self, groupIdx):
        ret = True
        group = self.groups[groupIdx]
        filePath = os_path.join(self.favDir, IPTVFavourites.FILE_NAME_MACRO % group['group_id'])
        try:
            items = []
            for favItem in group['items']:
                items.append( favItem.getAsDict() )
            data = json.dumps(items)
            self._saveToFile(filePath, data)
        except:
            printExc()
            self.lastError += _('Error writing file [%s].\n') % filePath
            ret = False
        return ret
    
    def _saveGroups(self):
        ret = True
        groups = list(self.groups)
        try:
            for item in groups: item.pop("items", None)
            filePath = os_path.join(self.favDir, IPTVFavourites.GROUPS_FILE_NAME)
            data = json.dumps(groups)
            self._saveToFile(filePath, data)
        except:
            self.lastError += _('Error writing file [%s].\n') % filePath
            ret = False
        return ret
        
    def _saveToFile(self, filePath, data, encoding='utf-8'):
        with codecs.open(filePath, 'w', encoding, 'replace') as fp:
            fp.write(data)
            
    def _loadFromFile(self, filePath, encoding='utf-8'):
        with codecs.open(filePath, 'r', encoding, 'replace') as fp:
            return fp.read()
        
        