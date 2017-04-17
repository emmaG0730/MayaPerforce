from P4 import P4, P4Exception, Progress, OutputHandler

import Perforce.Utils as Utils

class TestOutputAndProgress(Progress, OutputHandler):

    def __init__(self, ui):
        Progress.__init__(self)
        OutputHandler.__init__(self)
        self.totalFiles = 0
        self.totalSizes = 0
        self.ui = ui
        self.ui.setMinimum(0)
        self.ui.setHandler(self)

        self.shouldCancel = False

    def setCancel(self, val):
        self.shouldCancel = val

    def outputStat(self, stat):
        if 'totalFileCount' in stat:
            self.totalFileCount = int(stat['totalFileCount'])
            print "TOTAL FILE COUNT: ", self.totalFileCount
        if 'totalFileSize' in stat:
            self.totalFileSize = int(stat['totalFileSize'])
            print "TOTAL FILE SIZE: ", self.totalFileSize
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputInfo(self, info):
        AppUtils.refresh()
        print "INFO :", info
        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def outputMessage(self, msg):
        AppUtils.refresh()
        print "Msg :", msg

        if self.shouldCancel:
            return OutputHandler.REPORT | OutputHandler.CANCEL
        else:
            return OutputHandler.HANDLED

    def init(self, type):
        AppUtils.refresh()
        print "Begin :", type
        self.type = type
        self.ui.incrementCurrent()

    def setDescription(self, description, unit):
        AppUtils.refresh()
        print "Desc :", description, unit
        pass

    def setTotal(self, total):
        AppUtils.refresh()
        print "Total :", total
        self.ui.setMaximum(total)
        pass

    def update(self, position):
        AppUtils.refresh()
        print "Update : ", position
        self.ui.setValue(position)
        self.position = position

    def done(self, fail):
        AppUtils.refresh()
        print "Failed :", fail
        self.fail = fail