import threading
import sys
import xbmc
import xbmcgui
import xbmcvfs
from artutils import process_method_on_list, KodiDb
from utils import log_msg, get_current_content_type


class SearchDialog(xbmcgui.WindowXMLDialog):

    search_thread = None
    search_string = ""

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self.action_exitkeys_id = [10, 13]
        self.search_thread = SearchBackgroundThread()
        self.search_thread.set_dialog(self)
        self.search_thread.start()

    def onAction(self, action):
        '''triggers on kodi navigation events'''
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            # backspace
            self.remove_char()

        elif action.getId() in (11, ):
            # info key
            self.show_info()

        else:
            self.onActionTextBox(action)

    def close_dialog(self, action=None):
        '''stop background thread and close the dialog'''
        self.search_thread.stop_running()
        self.close()

    def remove_char(self):
        '''remove character from query string'''
        if (len(self.search_string) == 0 or self.search_string == " "):
            self.close_dialog()
        else:
            if(len(self.search_string) == 1):
                search_term = " "
            else:
                search_term = self.search_string[:-1]
            self.setFocusId(3056)
            self.getControl(3010).setLabel(search_term)
            self.search_string = search_term
            self.search_thread.set_search(search_term)

    def onActionTextBox(self, act):
        '''special handler to allow direct typing to search'''
        ACTION_NUMBER_0 = 58
        ACTION_NUMBER_9 = 67
        action = act.getId()
        button = act.getButtonCode()

        # Upper-case values
        if button >= 0x2f041 and button <= 0x2f05b:
            self.add_character(chr(button - 0x2F000))

        # Lower-case values
        if button >= 0xf041 and button <= 0xf05b:
            self.add_character(chr(button - 0xEFE0))

        # Numbers
        if action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            self.add_character(chr(action - ACTION_NUMBER_0 + 48))

        # Backspace
        if button == 0xF008:
            if len(self.search_string) >= 1:
                self.remove_char()

        # Delete
        if button == 0xF02E:
            self.clear_search()

        # Space
        if button == 0xF020:
            self.add_character(" ")

        if xbmc.getCondVisibility("Window.IsVisible(10111)"):
            # close shutdown window if visible
            xbmc.executebuiltin("w.close(10111)")

    def focus_char(self, char):
        '''focus specified character'''
        alphanum = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                    'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3',
                    '4', '5', '6', '7', '8', '9', '', ' '].index(str(char).upper())
        self.setFocusId(3020 + alphanum)

    def onClick(self, control_id):
        '''Kodi builtin: triggers if window is clicked'''
        if control_id == 3020:
            self.add_character("A")
        elif control_id == 3021:
            self.add_character("B")
        elif control_id == 3022:
            self.add_character("C")
        elif control_id == 3023:
            self.add_character("D")
        elif control_id == 3024:
            self.add_character("E")
        elif control_id == 3025:
            self.add_character("F")
        elif control_id == 3026:
            self.add_character("G")
        elif control_id == 3027:
            self.add_character("H")
        elif control_id == 3028:
            self.add_character("I")
        elif control_id == 3029:
            self.add_character("J")
        elif control_id == 3030:
            self.add_character("K")
        elif control_id == 3031:
            self.add_character("L")
        elif control_id == 3032:
            self.add_character("M")
        elif control_id == 3033:
            self.add_character("N")
        elif control_id == 3034:
            self.add_character("O")
        elif control_id == 3035:
            self.add_character("P")
        elif control_id == 3036:
            self.add_character("Q")
        elif control_id == 3037:
            self.add_character("R")
        elif control_id == 3038:
            self.add_character("S")
        elif control_id == 3039:
            self.add_character("T")
        elif control_id == 3040:
            self.add_character("U")
        elif control_id == 3041:
            self.add_character("V")
        elif control_id == 3042:
            self.add_character("W")
        elif control_id == 3043:
            self.add_character("X")
        elif control_id == 3044:
            self.add_character("Y")
        elif control_id == 3045:
            self.add_character("Z")
        elif control_id == 3046:
            self.add_character("0")
        elif control_id == 3047:
            self.add_character("1")
        elif control_id == 3048:
            self.add_character("2")
        elif control_id == 3049:
            self.add_character("3")
        elif control_id == 3050:
            self.add_character("4")
        elif control_id == 3051:
            self.add_character("5")
        elif control_id == 3052:
            self.add_character("6")
        elif control_id == 3053:
            self.add_character("7")
        elif control_id == 3054:
            self.add_character("8")
        elif control_id == 3055:
            self.add_character("9")
        elif control_id == 3056:
            self.remove_char()
        elif control_id == 3057:
            self.add_character(" ")
        elif control_id == 3058:
            self.clear_search()
        elif control_id == 3010:
            dialog = xbmcgui.Dialog()
            search_term = w.input(xbmc.getLocalizedString(16017), type=xbmcgui.INPUT_ALPHANUM)
            self.getControl(3010).setLabel(search_term)
            self.search_string = search_term
            self.search_thread.set_search(search_term)
        elif control_id in [3110, 3111, 3112]:
            self.show_info()

    def clear_search(self):
        '''clears the search textbox'''
        self.setFocusId(3058)
        self.getControl(3010).setLabel(" ")
        self.search_string = ""
        self.search_thread.set_search("")

    def add_character(self, char):
        '''add character to our search textbox'''
        self.focus_char(char)
        search_term = self.search_string + char
        self.getControl(3010).setLabel(search_term)
        self.search_string = search_term
        self.search_thread.set_search(search_term)

    def show_info(self):
        '''show info dialog for selected item'''
        control_id = self.getFocusId()
        listitem = self.getControl(control_id).getSelectedItem()
        from infodialog import DialogVideoInfo
        win = DialogVideoInfo("DialogVideoInfo.xml", "", listitem=listitem)
        win.doModal()
        del dialogin


class SearchBackgroundThread(threading.Thread):
    '''Background thread to complement our search dialog,
    fills the listing while UI keeps responsive'''
    active = True
    dialog = None
    search_string = ""

    def __init__(self, *args):
        xbmc.log("SearchBackgroundThread Init")
        threading.Thread.__init__(self, *args)
        self.kodidb = KodiDb()

    def set_search(self, searchstr):
        '''set search query'''
        self.search_string = searchstr

    def stop_running(self):
        '''stop thread end exit'''
        self.active = False

    def set_dialog(self, dialog):
        '''set the active dialog to perform actions'''
        self.dialog = dialog

    def run(self):
        '''Main run loop for the background thread'''
        last_searchstring = ""
        monitor = xbmc.Monitor()
        while not monitor.abortRequested() and self.active:
            if(self.search_string != last_searchstring):
                last_searchstring = self.search_string
                self.do_search(self.search_string)
            monitor.waitForAbort(1)
        del monitor

    def do_search(self, search_term):
        '''scrape results for search query'''

        movies_list = self.w.getControl(3110)
        series_list = self.w.getControl(3111)
        episodes_list = self.w.getControl(3112)

        # clear current values
        movies_list.reset()
        series_list.reset()
        episodes_list.reset()

        if len(search_term) == 0:
            return

        filters = [{"operator": "contains", "field": "title", "value": search_term}]

        # Process movies
        items = self.kodidb.movies(filters=filters)
        items = process_method_on_list(self.kodidb.prepare_listitem, items)
        result = []
        for item in items:
            result.append(self.kodidb.create_listitem(item, False))
        movies_list.addItems(result)

        # Process tvshows
        items = self.kodidb.tvshows(filters=filters)
        items = process_method_on_list(self.kodidb.prepare_listitem, items)
        result = []
        for item in items:
            item["file"] = 'videodb://tvshows/titles/%s' % item['tvshowid']
            item["isFolder"] = True
            result.append(self.kodidb.create_listitem(item, False))
        series_list.addItems(result)

        # Process episodes
        items = self.kodidb.episodes(filters=filters)
        items = process_method_on_list(self.kodidb.prepare_listitem, items)
        result = []
        for item in items:
            result.append(self.kodidb.create_listitem(item, False))
        episodes_list.addItems(result)
