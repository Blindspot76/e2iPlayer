# -*- coding: utf-8 -*-
#
#  E2iPlayer On Screen Keyboard based on Windows keyboard layouts
#
#  $Id$
#
# 
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from enigma import ePoint, gFont, gRGB, getDesktop
from Tools.LoadPixmap import LoadPixmap
from Components.Label import Label
from Components.Input import Input
from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

from Plugins.Extensions.IPTVPlayer.components.cover import Cover3
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetIconDir
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _

class E2iVirtualKeyBoard(Screen):
    SK_NONE  = 0
    SK_SHIFT = 1
    SK_CTRL  = 2
    SK_ALT   = 4
    SK_CAPSLOCK = 8
    KEYIDMAP =[
               [0 ,  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
               [1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15],
               [16, 16,   17, 18,   19, 20,  21,  22,  23,  24,  25,  26,  27,  28,  29],
               [30, 30,   31, 32,   33, 34,  35,  36,  37,  38,  39,  40,  41,  42,  42],
               [43, 43,   44, 45,   46, 47,  48,  49,  50,  51,  52,  53,  54,  55,  55],
               [56, 56,   57, 58,   59, 59,  59,  59,  59,  59,  59,  59,  60,  61,  62],
              ]

    def prepareSkin(self):
        # screen size
        # we do not want borders, so make the screen lager than a desktop
        sz_w = getDesktop(0).size().width() 
        sz_h = getDesktop(0).size().height()
        x = (sz_w - 750) / 2
        y = sz_h - 350
        
        skinTab = ["""<screen position="center,center" size="%d,%d" title="E2iPlayer virtual keyboard">""" %( sz_w, sz_h ) ]
        
        def _addPixmapWidget(name, x, y, w, h, p):
            skinTab.append('<widget name="%s" zPosition="%d" position="%d,%d" size="%d,%d" transparent="1" alphatest="blend" />' % (name, p, x, y, w, h))
            
        def _addMarker(name, x, y, w, h, p, color):
            skinTab.append('<widget name="%s" zPosition="%d" position="%d,%d" size="%d,%d" noWrap="1" font="Regular;2" valign="center" halign="center" foregroundColor="%s" backgroundColor="%s" />' % (name, p, x, y, w, h, color, color))
        
        def _addButton(name, x, y, w, h, p):
            _addPixmapWidget(name, x, y, w,  h, p)
            if name in [1, 16, 29, 30, 42, 43, 55, 57, 58, 60]:
                font = 20
                color = '#1688b2'
                align = 'center'
            elif name in [61, 62]:
                font = 30
                color = '#1688b2'
                align = 'center'
            elif name == 56:
                font = 20
                color = '#1688b2'
                align = 'left'
                x += 40
                w -= 40
            else:
                font = 20
                color = '#404551'
                align = 'center'
            skinTab.append('<widget name="_%s" zPosition="%d" position="%d,%d" size="%d,%d" transparent="1" noWrap="1" font="Regular;%s" valign="center" halign="%s" foregroundColor="#ffffff" backgroundColor="%s" />' % (name, p+2, x, y, w, h, font, align, color))
        
        skinTab.append('<widget name="header" zPosition="%d" position="%d,%d" size="%d,%d"  transparent="1" noWrap="1" font="Regular;20" valign="center" halign="left" foregroundColor="#ffffff" backgroundColor="#000000" />' % (2,  x+5, y-50,  740, 36))
        skinTab.append('<widget name="text"   zPosition="%d" position="%d,%d" size="%d,%d"  transparent="1" noWrap="1" font="Regular;26" valign="center" halign="left" />' % (2,  x+5, y+7,  740, 36))
        _addPixmapWidget(0, x, y,  750, 50, 1)
        _addPixmapWidget('e_m', 0, 0,  750, 50, 5)
        _addPixmapWidget('k_m', 0, 0,   50, 50, 5)
        _addPixmapWidget('k2_m', 0, 0, 100, 50, 5)
        _addPixmapWidget('k3_m', 0, 0, 400, 50, 5)
        
        for i in range(0, 15):
            _addButton(i+1, x+50*i, y+10+50*1, 50,  50, 1)
        _addPixmapWidget('b', x+50*14+7, y+10+50*1+15, 41,  35, 3) # backspace icon
        
        _addButton(16, x, y+10+50*2, 100,  50, 1)
        for i in range(0, 14):
            _addButton(i+17, x+50*(i+2), y+10+50*2, 50,  50, 1)
        
        _addButton(30, x, y+10+50*3, 100,  50, 1)
        for i in range(0, 13):
            _addButton(i+31, x+50*(i+2), y+10+50*3, 50,  50, 1)
        _addButton(42, x+50*13, y+10+50*3, 100,  50, 1)
        
        _addButton(43, x, y+10+50*4, 100,  50, 1)
        for i in range(0, 13):
            _addButton(i+44, x+50*(i+2), y+10+50*4, 50,  50, 1)
        _addButton(55, x+50*13, y+10+50*4, 100,  50, 1)
        
        _addPixmapWidget('l', x+10, y+10+50*5+14, 26,  26, 3) # language icon
        _addButton(56, x,       y+10+50*5, 100,  50, 1)
        _addButton(57, x+50*2,  y+10+50*5,  50,  50, 1)
        _addButton(58, x+50*3,  y+10+50*5,  50,  50, 1)
        _addButton(59, x+50*4,  y+10+50*5, 400,  50, 1)
        _addButton(60, x+50*12, y+10+50*5,  50,  50, 1)
        _addButton(61, x+50*13, y+10+50*5,  50,  50, 1)
        _addButton(62, x+50*14, y+10+50*5,  50,  50, 1)
        
        # Backspace
        #_addMarker('m_0', x+10,       y+10+50*2+40, 80,  3, 2, '#ed1c24')
        _addMarker('m_0', x+50*14+10, y+10+50*1+40, 30,  3, 2, '#ed1c24')

        # Shift
        _addMarker('m_1', x+10,       y+10+50*4+40, 80,  3, 2, '#3f48cc')
        _addMarker('m_2', x+50*13+10, y+10+50*4+40, 80,  3, 2, '#3f48cc')

        # Alt
        _addMarker('m_3', x+50*3+10,  y+10+50*5+40, 30,  3, 2, '#fff200')
        _addMarker('m_4', x+50*12+10, y+10+50*5+40, 30,  3, 2, '#fff200')

        # Enter
        _addMarker('m_5', x+50*13+10, y+10+50*3+40, 80,  3, 2, '#22b14c')

        skinTab.append('</screen>')
        return '\n'.join(skinTab)

    def __init__(self, session, title="", text="", additionalParams={}):
        self.session = session

        self.skin = self.prepareSkin()

        Screen.__init__(self, session)

        self.onLayoutFinish.append(self.setGraphics)
        self.onShown.append(self.onWindowShow)

        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
        {
            "ok":    self.keyOK,
            "back":  self.keyBack,
            "left":  self.keyLeft,
            "right": self.keyRight,
            "up":    self.keyUp,
            "down":  self.keyDown,
            "red":   self.keyRed,
            "green": self.keyGreen,
            "yellow":self.keyYellow,
            "blue":  self.keyBlue,
        }, -1)

        self.graphics = {}
        for key in ['pb', 'pr', 'pg', 'py', 'l', 'b', 'e', 'e_m', 'k', 'k_m', 'k_s', 'k2_m', 'k2_s', 'k3', 'k3_m']:
            self.graphics[key] = LoadPixmap(GetIconDir('e2ivk/%s.png') % key)

        for i in range(0, 63):
            self[str(i)] = Cover3()

        for key in ['l', 'b', 'e_m', 'k_m', 'k2_m', 'k3_m']:
            self[key] = Cover3()
            
        for i in range(1, 63):
            self['_%s' % i] = Label(" ")
        
        for m in range(6):
            self['m_%d' % m] = Label(" ")

        self.graphicsMap = {'0':'e', '1':'k_s', '15':'k_s', '29':'k_s', '57':'k_s', '58':'k_s', '60':'k_s', '61':'k_s', '62':'k_s', '59':'k3',
                            '16':'k2_s', '30':'k2_s', '42':'k2_s', '43':'k2_s', '55':'k2_s', '56':'k2_s'}
        
        self.markerMap = {'0':'e_m', '59':'k3_m', '16':'k2_m', '30':'k2_m', '42':'k2_m', '43':'k2_m', '55':'k2_m', '56':'k2_m'}

        self.header = title if title else _('Enter the text')
        self.startText = text
        self.oskLayout = additionalParams.get('osk_layout', config.plugins.iptvplayer.osk_layout.value)
        
        self["text"] = Input(text=self.startText)
        self["header"] = Label(" ")

        self.colMax = len(self.KEYIDMAP[0])
        self.rowMax = len(self.KEYIDMAP)

        self.rowIdx = 1
        self.colIdx = 0

        self.colors = {'normal':gRGB(int('ffffff', 0x10)), 'selected':gRGB(int('39b54a', 0x10)), 'deadkey':gRGB(int('0000ff', 0x10)), 'ligature':gRGB(int('ff3c00', 0x10)), 'inactive':gRGB(int('979697', 0x10))}

        self.specialKeyState = self.SK_NONE
        self.currentKeyboardLayout = {}

        self.deadKey = u''

    def onWindowShow(self):
        self.onShown.remove(self.onWindowShow)
        self.setTitle(_('Virtual Keyboard'))
        self["header"].setText(self.header)
        
        self["text"].right()
        self["text"].currPos = len(self.startText)
        self["text"].right()
        #self.oskLayout
        self.loadKeyboardLayout('polish-p')

    def setGraphics(self):
        self.onLayoutFinish.remove(self.setGraphics)
        
        for i in range(0, 63):
            key = self.graphicsMap.get(str(i), 'k')
            self[str(i)].setPixmap( self.graphics[key] )
        
        for key in ['e_m', 'k_m', 'k2_m', 'k3_m']:
            self[key].hide()
            self[key].setPixmap( self.graphics[key] )
        
        self['b'].setPixmap( self.graphics['b'] )
        self['l'].setPixmap( self.graphics['l'] )
        
        keyID = self.KEYIDMAP[self.rowIdx][self.colIdx]
        self.moveMarker(-1, keyID)
        
        self.setSpecialKeyLabels()

    def setSpecialKeyLabels(self):
        self['_1'].setText('Esc')
        self['_16'].setText(_('Clear'))
        self['_29'].setText('Del')
        self['_30'].setText('Caps')
        self['_42'].setText('Enter')
        self['_43'].setText('Shift')
        self['_55'].setText('Shift')
        self['_57'].setText('Ctrl')
        self['_58'].setText('Alt')
        self['_60'].setText('Alt')
        self['_61'].setText(u'\u2190'.encode('utf-8'))
        self['_62'].setText(u'\u2192'.encode('utf-8'))
        
        self['_56'].setText('PL') # test

    def handleArrowKey(self, dx=0, dy=0):
        oldKeyId = self.KEYIDMAP[self.rowIdx][self.colIdx]
        keyID = oldKeyId
        if dx != 0 and keyID == 0: 
            return

        if dx != 0: # left/right
            colIdx = self.colIdx
            while True:
                colIdx += dx
                if colIdx < 0: colIdx = self.colMax -1
                elif colIdx >= self.colMax: colIdx = 0
                if keyID != self.KEYIDMAP[self.rowIdx][colIdx]:
                    self.colIdx = colIdx
                    break
        elif dy != 0: # up/down
            rowIdx = self.rowIdx
            while True:
                rowIdx += dy
                if rowIdx < 0: rowIdx = self.rowMax -1
                elif rowIdx >= self.rowMax: rowIdx = 0
                if keyID != self.KEYIDMAP[rowIdx][self.colIdx]:
                    self.rowIdx = rowIdx
                    break

        # center the cursor only when left/right
        if dx != 0:
            keyID = self.KEYIDMAP[self.rowIdx][self.colIdx]
            
            # find max
            maxKeyX = self.colIdx
            for idx in range(self.colIdx+1, self.colMax):
                if keyID == self.KEYIDMAP[self.rowIdx][idx]:
                    maxKeyX = idx
                else:
                    break
            # find min
            minKeyX = self.colIdx
            for idx in range(self.colIdx-1, -1, -1):
                if keyID == self.KEYIDMAP[self.rowIdx][idx]:
                    minKeyX = idx
                else:
                    break
            if maxKeyX - minKeyX > 2:
                self.colIdx = (maxKeyX + minKeyX) / 2

        self.moveMarker(oldKeyId, self.KEYIDMAP[self.rowIdx][self.colIdx])

    def moveMarker(self, oldKeyId, newKeyId):
        if oldKeyId != -1:
            keyid = str(oldKeyId)
            marker = self.markerMap.get(keyid, 'k_m') 
            self[marker].hide()

        if newKeyId != -1:
            keyid = str(newKeyId)
            marker = self.markerMap.get(keyid, 'k_m') 
            self[marker].instance.move(ePoint(self[keyid].position[0], self[keyid].position[1]))
            self[marker].show()

        self.currentKeyId = newKeyId

    def handleKeyId(self, keyid):
        if keyid == 0:    # OK
            keyid = 42

        if keyid == 1:  # Escape
            self.close(None)
            return
        elif keyid == 15: # Backspace
            self["text"].deleteBackward()
            return
        elif keyid == 29: # Delete
            self["text"].delete()
            return
        elif keyid == 16: # Clear
            self["text"].deleteAllChars()
            self["text"].update()
            return
        elif keyid == 56: # Language
            pass
        elif keyid == 61: # Left
            self["text"].left()
            return
        elif keyid == 62: # Right
            self["text"].right()
            return
        elif keyid == 42: # Enter
            try:
                # make sure that Input component return valid UTF-8 data
                text = self["text"].getText().decode('UTF-8').encode('UTF-8')
            except Exception:
                text = ''
                printExc()
            self.close(text)
            return
        elif keyid == 30:       # Caps Lock
            self.specialKeyState ^= self.SK_CAPSLOCK
            self.updateKeysLabels()
            self.updateSpecialKey([30], self.specialKeyState & self.SK_CAPSLOCK)
            return
        elif keyid in [43, 55]: # Shift
            self.specialKeyState ^= self.SK_SHIFT
            self.updateKeysLabels()
            self.updateSpecialKey([43, 55], self.specialKeyState & self.SK_SHIFT)
            return
        elif keyid in [58, 60]: # ALT
            self.specialKeyState ^= self.SK_ALT
            self.updateKeysLabels()
            self.updateSpecialKey([58, 60], self.specialKeyState & self.SK_ALT)
            return
        elif keyid == 57:       # CTRL
            self.specialKeyState ^= self.SK_CTRL
            self.updateKeysLabels()
            self.updateSpecialKey([57], self.specialKeyState & self.SK_CTRL)
            return
        else:
            updateKeysLabels = False
            ret = 0
            text = u''
            val = self.getKeyValue(keyid)

            if val:
                for special in [(self.SK_CTRL, [57]), (self.SK_ALT, [58, 60]), (self.SK_SHIFT, [43, 55])]:
                    if self.specialKeyState & special[0]:
                        self.specialKeyState ^= special[0]
                        self.updateSpecialKey(special[1], 0)
                        ret = None
                        updateKeysLabels = True

            if val:
                if self.deadKey:
                    if val in self.currentKeyboardLayout['deadkeys'].get(self.deadKey, {}):
                        text = self.currentKeyboardLayout['deadkeys'][self.deadKey][val]
                    else:
                        text = self.deadKey + val
                    self.deadKey = u''
                    updateKeysLabels = True
                elif val in self.currentKeyboardLayout['deadkeys']:
                    self.deadKey = val
                    updateKeysLabels = True
                else:
                    text = val

                for letter in text:
                    try:
                        self["text"].insertChar(letter, self["text"].currPos, False, True)
                        self["text"].innerright()
                        self["text"].update()
                    except Exception:
                        printExc()
                ret = None

            if updateKeysLabels:
                self.updateKeysLabels()
            return ret
        return 0

    def loadKeyboardLayout(self, language):
        self.currentKeyboardLayout = {'layout':{2:{0:u'`',1:u'~',8:u'`',9:u'~'},3:{0:u'1',1:u'!',8:u'1',9:u'!'},4:{0:u'2',1:u'@',8:u'2',9:u'@'},5:{0:u'3',1:u'#',8:u'3',9:u'#'},6:{0:u'4',1:u'$',8:u'4',9:u'$'},7:{0:u'5',1:u'%',8:u'5',9:u'%'},8:{0:u'6',1:u'^',8:u'6',9:u'^'},9:{0:u'7',1:u'&',8:u'7',9:u'&'},10:{0:u'8',1:u'*',8:u'8',9:u'*'},11:{0:u'9',1:u'(',8:u'9',9:u'('},12:{0:u'0',1:u')',8:u'0',9:u')'},13:{0:u'-',1:u'_',8:u'-',9:u'_'},14:{0:u'=',1:u'+',8:u'=',9:u'+'},17:{0:u'q',1:u'Q',8:u'Q',9:u'q'},18:{0:u'w',1:u'W',8:u'W',9:u'w'},19:{0:u'e',1:u'E',6:u'\u0119',7:u'\u0118',8:u'E',9:u'e',14:u'\u0118',15:u'\u0119'},20:{0:u'r',1:u'R',8:u'R',9:u'r'},21:{0:u't',1:u'T',8:u'T',9:u't'},22:{0:u'y',1:u'Y',8:u'Y',9:u'y'},23:{0:u'u',1:u'U',6:u'\u20ac',8:u'U',9:u'u',14:u'\u20ac'},24:{0:u'i',1:u'I',8:u'I',9:u'i'},25:{0:u'o',1:u'O',6:u'\xf3',7:u'\xd3',8:u'O',9:u'o',14:u'\xd3',15:u'\xf3'},26:{0:u'p',1:u'P',8:u'P',9:u'p'},27:{0:u'[',1:u'{',2:u'\x1b',8:u'[',9:u'{',10:u'\x1b'},28:{0:u']',1:u'}',2:u'\x1d',8:u']',9:u'}',10:u'\x1d'},31:{0:u'a',1:u'A',6:u'\u0105',7:u'\u0104',8:u'A',9:u'a',14:u'\u0104',15:u'\u0105'},32:{0:u's',1:u'S',6:u'\u015b',7:u'\u015a',8:u'S',9:u's',14:u'\u015a',15:u'\u015b'},33:{0:u'd',1:u'D',8:u'D',9:u'd'},34:{0:u'f',1:u'F',8:u'F',9:u'f'},35:{0:u'g',1:u'G',8:u'G',9:u'g'},36:{0:u'h',1:u'H',8:u'H',9:u'h'},37:{0:u'j',1:u'J',8:u'J',9:u'j'},38:{0:u'k',1:u'K',8:u'K',9:u'k'},39:{0:u'l',1:u'L',6:u'\u0142',7:u'\u0141',8:u'L',9:u'l',14:u'\u0141',15:u'\u0142'},40:{0:u';',1:u':',2:u'\x1d',8:u';',9:u':',10:u'\x1d'},41:{0:u"'",1:u'"',8:u"'",9:u'"'},44:{0:u'z',1:u'Z',6:u'\u017c',7:u'\u017b',8:u'Z',9:u'z',14:u'\u017b',15:u'\u017c'},45:{0:u'x',1:u'X',6:u'\u017a',7:u'\u0179',8:u'X',9:u'x',14:u'\u0179',15:u'\u017a'},46:{0:u'c',1:u'C',6:u'\u0107',7:u'\u0106',8:u'C',9:u'c',14:u'\u0106',15:u'\u0107'},47:{0:u'v',1:u'V',8:u'V',9:u'v'},48:{0:u'b',1:u'B',8:u'B',9:u'b'},49:{0:u'n',1:u'N',6:u'\u0144',7:u'\u0143',8:u'N',9:u'n',14:u'\u0143',15:u'\u0144'},50:{0:u'm',1:u'M',8:u'M',9:u'm'},51:{0:u',',1:u'<',8:u',',9:u'<'},52:{0:u'.',1:u'>',8:u'.',9:u'>'},53:{0:u'/',1:u'?',8:u'/',9:u'?'},54:{0:u'\\',1:u'|',2:u'\x1c',8:u'\\',9:u'|',10:u'\x1c'},59:{0:u' ',1:u' ',2:u' ',8:u' ',9:u' ',10:u' '}},'deadkeys':{u'~':{u'a':u'\u0105',u'A':u'\u0104',u'c':u'\u0107',u'Z':u'\u017b',u'e':u'\u0119',u' ':u'~',u'N':u'\u0143',u'l':u'\u0142',u'o':u'\xf3',u'n':u'\u0144',u's':u'\u015b',u'O':u'\xd3',u'E':u'\u0118',u'X':u'\u0179',u'x':u'\u017a',u'C':u'\u0106',u'z':u'\u017c',u'S':u'\u015a',u'L':u'\u0141'}}}
        self.updateKeysLabels()

    def updateSpecialKey(self, keysidTab, state):
        if state:
            color = self.colors['selected']
        else:
            color = self.colors['normal']

        for keyid in keysidTab:
            self['_%s' % keyid].instance.setForegroundColor( color )

    def getKeyValue(self, keyid):
        state = self.specialKeyState
        # we treat both Alt keys as AltGr
        if self.specialKeyState & self.SK_ALT and not (self.specialKeyState & self.SK_CTRL):
            state ^= self.SK_CTRL
        key = self.currentKeyboardLayout['layout'][keyid]
        if state in key:
            val = key[state]
        else:
            val = u''
        return val

    def updateNormalKeyLabel(self, keyid):

        val = self.getKeyValue(keyid)
        if not self.deadKey:
            if len(val) > 1:
                color = self.colors['ligature']
            elif val in self.currentKeyboardLayout['deadkeys']:
                color = self.colors['deadkey']
            else:
                color = self.colors['normal']
        elif val in self.currentKeyboardLayout['deadkeys'].get(self.deadKey, {}):
            val = self.currentKeyboardLayout['deadkeys'][self.deadKey][val]
            color = self.colors['normal']
        else:
            color = self.colors['inactive']

        skinKey = self['_%s' % keyid]
        skinKey.instance.setForegroundColor( color )
        skinKey.setText(val.encode('utf-8'))

    def updateKeysLabels(self):
        for rangeItem in [(2, 14), (17, 28), (31, 41), (44, 54), (59, 59)]:
            for keyid in range(rangeItem[0], rangeItem[1]+1):
                self.updateNormalKeyLabel(keyid)

    def keyRed(self):
        self.handleKeyId(15)

    def keyGreen(self):
        self.handleKeyId(42)

    def keyYellow(self):
        self.handleKeyId(60)

    def keyBlue(self):
        self.handleKeyId(43)

    def keyOK(self):
        self.handleKeyId(self.currentKeyId)

    def keyBack(self):
        self.close(None)

    def keyUp(self):
        printDBG('keyUp')
        self.handleArrowKey(0, -1)

    def keyDown(self):
        printDBG('keyDown')
        self.handleArrowKey(0, 1)

    def keyLeft(self):
        printDBG('keyLeft')
        if self.currentKeyId == 0:
            self["text"].left()
        else:
            self.handleArrowKey(-1, 0)

    def keyRight(self):
        printDBG('keyRight')
        if self.currentKeyId == 0:
            self["text"].right()
        else:
            self.handleArrowKey(1, 0)

