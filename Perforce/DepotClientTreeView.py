import sys
import os
from PySide import QtCore, QtGui

from P4 import P4, P4Exception

# http://stackoverflow.com/questions/32229314/pyqt-how-can-i-set-row-heights-of-qtreeview


class TreeItem(object):

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.data = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def popChild(self):
        if self.childItems:
            self.childItems.pop()

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0


def reconnect():
    p4.disconnect()
    p4.connect()
    p4.password = "contact_dev"
    p4.run_login()


def epochToTimeStr(time):
    import datetime
    return datetime.datetime.utcfromtimestamp(int(time)).strftime("%d/%m/%Y %H:%M:%S")


def perforceListDir(p4path):
    result = []

    if p4path[-1] == '/' or p4path[-1] == '\\':
        p4path = p4path[:-1]

    path = "{0}/{1}".format(p4path, '*')

    isDepotPath = p4path.startswith("//depot")

    dirs = []
    files = []

    # Dir silently does nothing if there are no dirs
    try:
        dirs = p4.run_dirs(path)
    except P4Exception:
        pass

    # Files will return an exception if there are no files in the dir
    # Stupid inconsistency imo
    try:
        if isDepotPath:
            files = p4.run_files(path)
        else:
            tmp = p4.run_have(path)
            for fileItem in tmp:
                files += p4.run_fstat(fileItem['clientFile'])
    except P4Exception:
        pass

    result = []

    for dir in dirs:
        if isDepotPath:
            dirName = dir['dir'][8:]
        else:
            dirName = dir['dir']

        tmp = {'name': os.path.basename(dirName),
               'path': dir['dir'],
               'time': '',
               'type': 'Folder',
               'change': ''
               }
        result.append(tmp)

    for fileItem in files:
        if isDepotPath:
            deleteTest = p4.run("filelog", "-t", fileItem['depotFile'])[0]
            isDeleted = deleteTest['action'][0] == "delete"
            fileType = fileItem['type']
            if isDeleted:
                fileType = "{0} [Deleted]".format(fileType)
            # Remove //depot/ from the path for the 'pretty' name
            tmp = {'name': os.path.basename(fileItem['depotFile'][8:]),
                   'path': fileItem['depotFile'],
                   'time': epochToTimeStr(fileItem['time']),
                   'type': fileType,
                   'change': fileItem['change']
                   }
            result.append(tmp)
        else:
            deleteTest = p4.run("filelog", "-t", fileItem['clientFile'])[0]
            isDeleted = deleteTest['action'][0] == "delete"
            fileType = fileItem['headType']
            if isDeleted:
                fileType = "{0} [Deleted]".format(fileType)
            tmp = {'name': os.path.basename(fileItem['clientFile']),
                   'path': fileItem['clientFile'],
                   'time': epochToTimeStr(fileItem['headModTime']),
                   'type': fileType,
                   'change': fileItem['headChange']
                   }
            result.append(tmp)

    return sorted(result, key=lambda k: k['name'])


def perforceIsDir(p4path):
    try:
        if p4path[-1] == '/' or p4path[-1] == '\\':
            p4path = p4path[:-1]
        result = p4.run_dirs(p4path)
        return len(result) > 0
    except P4Exception as e:
        print e
        return False


def p4Filelist(dir, findDeleted=False):
    p4path = '/'.join([dir, '*'])
    try:
        files = p4.run_filelog("-t", p4path)
    except P4Exception as e:
        print e
        return []

    results = []

    for x in files:
        latestRevision = x.revisions[0]
        print latestRevision.action, latestRevision.depotFile

        if not findDeleted and latestRevision.action == 'delete':
            continue
        else:
            results.append({'name': latestRevision.depotFile,
                            'action': latestRevision.action,
                            'change': latestRevision.change,
                            'time': latestRevision.time,
                            'type': latestRevision.type
                            }
                           )

    filesInCurrentChange = p4.run_opened(p4path)
    for x in filesInCurrentChange:
        print x
        results.append({'name': x['clientFile'],
                        'action': x['action'],
                        'change': x['change'],
                        'time': "",
                        'type': x['type']
                        }
                       )

    return results


class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(None)
        self.showDeleted = False

    def populate(self, rootdir="//depot", findDeleted=False):
        self.rootItem = TreeItem(None)
        self.showDeleted = findDeleted

        depotPath = False
        if "depot" in rootdir:
            depotPath = True

        p4path = '/'.join([rootdir, '*'])

        if depotPath:
            dirs = p4.run_dirs(p4path)
        else:
            dirs = p4.run_dirs('-H', p4path)

        for dir in dirs:
            dirName = os.path.basename(dir['dir'])
            # subDir = '/'.join( [rootdir, dirName )] )
            data = [dirName, "Folder", "", "", ""]

            treeItem = TreeItem(data, self.rootItem)
            self.rootItem.appendChild(treeItem)

            treeItem.appendChild(None)

            files = p4Filelist(dir['dir'], findDeleted)

            for f in files:
                fileName = os.path.basename(f['name'])
                data = [fileName, f['type'], f[
                    'time'], f['action'], f['change']]

                fileItem = TreeItem(data, treeItem)
                treeItem.appendChild(fileItem)

    # def populate(self, rootdir):
    #     rootdir = rootdir.replace('\\', '/')

    #     print "Scanning subfolders in {0}...".format(rootdir)

        # import maya.cmds as cmds
        # cmds.refresh()

        # def scanDirectoryPerforce(root, treeItem):
        #     change = p4.run_opened()

        #     for item in perforceListDir(root):
        # itemPath = "{0}/{1}".format(root, item['name'] ) # os.path.join(root, item)
        # print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+'
        # if perforceIsDir(itemPath) else '-', item['name'] )

        #         data = [ item['name'], item['type'], item['time'], item['change'] ]

        #         childDir = TreeItem( data, treeItem)
        #         treeItem.appendChild( childDir )

        #         tmpDir = TreeItem( [ "TMP", "", "", "" ], childDir )
        #         childDir.appendChild( None )

        # print itemPath, perforceIsDir( itemPath )
        # if perforceIsDir( itemPath ):
        # scanDirectoryPerforce(itemPath, childDir)

        # def scanDirectory(root, treeItem):
        #     for item in os.listdir(root):
        #         itemPath = os.path.join(root, item)
        #         print "{0}{1}{2}".format( "".join(["\t" for i in range(depth)]), '+' if os.path.isdir(itemPath) else '-', item)
        #         childDir = TreeItem( [item], treeItem)
        #         treeItem.appendChild( childDir )
        #         if os.path.isdir( itemPath ):
        #             scanDirectory(itemPath, childDir)

        # scanDirectoryPerforce(rootdir, self.rootItem )

        # print dirName
        # directory = "{0}:{1}".format(i, os.path.basename(dirName))
        # childDir = TreeItem( [directory], self.rootItem)
        # self.rootItem.appendChild( childDir )

        # for fname in fileList:
        #    childFile = TreeItem(fname, childDir)
        #    childDir.appendChild([childFile])

        #        for i,c  in enumerate("abcdefg"):
        #           child = TreeItem([i],self.rootItem)
        #           self.rootItem.appendChild(child)

    def columnCount(self, parent):
        return 5

    def data(self, index, role):
        column = index.column()
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            item = index.internalPointer()
            return item.data[column]
        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(20, 20)
        elif role == QtCore.Qt.DecorationRole:
            if column == 1:
                itemType = index.internalPointer().data[column]
                isDeleted = index.internalPointer().data[3] == 'delete'

                if isDeleted:
                    return QtGui.QIcon(r"/home/i7245143/src/MayaPerforce/Perforce/images/File0104.png")

                if itemType == "Folder":
                    return QtGui.QIcon(r"/home/i7245143/src/MayaPerforce/Perforce/images/File0059.png")
                elif "binary" in itemType:
                    return QtGui.QIcon(r"/home/i7245143/src/MayaPerforce/Perforce/images/File0315.png")
                elif "text" in itemType:
                    return QtGui.QIcon(r"/home/i7245143/src/MayaPerforce/Perforce/images/File0027.png")
                else:
                    return QtGui.QIcon(r"/home/i7245143/src/MayaPerforce/Perforce/images/File0106.png")

                icon = QtGui.QFileIconProvider(QtGui.QFileIconProvider.Folder)
                return icon
            else:
                return None

        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ["Filename", "Type", "Modification Time", "Action", "Change"][section]
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.childItems[row]
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        parentItem = index.internalPointer().parentItem
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rootrowcount(self):
        return len(self.rootItem.childItems)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return len(parentItem.childItems)


# allFiles = p4.run_files("//depot/...")
# hiddenFiles = p4.run_files("//depot/.../.*")

# testData = [['assets', '.place-holder'], ['assets', 'heroTV', 'lookDev', 'heroTV_lookDev.ma'], ['assets', 'heroTV', 'lookDev', 'heroTv_lookdev.ma'], ['assets', 'heroTV', 'modelling', '.place-holder'], ['assets', 'heroTV', 'modelling', 'Old_TV.obj'], ['assets', 'heroTV', 'modelling', 'heroTv_wip.ma'], ['assets', 'heroTV', 'rigging', '.place-holder'], ['assets', 'heroTV', 'texturing', '.place-holder'], ['assets', 'heroTV', 'workspace.mel'], ['assets', 'lookDevSourceimages', 'Garage.EXR'], ['assets', 'lookDevSourceimages', 'UVtile.jpg'], ['assets', 'lookDevSourceimages', 'macbeth_background.jpg'], ['assets', 'lookDevTemplate.ma'], ['assets', 'previs_WIP.ma'], ['assets', 'previs_slapcomp_WIP.ma'], ['audio', '.place-holder'], ['finalEdit', 'delivery', '.place-holder'], ['finalEdit', 'projects', '.place-holder'], ['finalEdit', 'test'], ['finalEdit', 'test.ma'], ['shots', '.place-holder'], ['shots', 'space', 'space_sh_010', 'cg', 'maya', 'scenes', 'spc_sh_010_animBuild_WIP.ma']]

# result = {}

# files = [ item['depotFile'][8:].split('/') for item in allFiles ]

# for item in files:
#     print item

# from collections import defaultdict
# deepestIndex, deepestPath = max(enumerate(files), key = lambda tup: len(tup[1]))


try:
    print p4
except:
    p4 = P4()
    p4.user = "tminor"
    p4.password = "contact_dev"
    p4.port = "ssl:52.17.163.3:1666"
    p4.connect()
    p4.run_login()

reconnect()

# Iterate upwards until we have the full path to the node


def fullPath(idx):
    result = [idx]

    parent = idx.parent()
    while True:
        if not parent.isValid():
            break
        result.append(parent)
        parent = parent.parent()

    return list(reversed(result))


def populateSubDir(idx, root="//depot", findDeleted=False):
    idxPathModel = fullPath(idx)
    idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
    idxFullPath = os.path.join(*idxPathSubDirs)

    if not idxFullPath:
        idxFullPath = "."

    # children = []

    p4path = '/'.join([root, idxFullPath, '*'])

    depotPath = False
    if "depot" in root:
        depotPath = True

    if depotPath:
        p4subdirs = p4.run_dirs(p4path)
    else:
        p4subdirs = p4.run_dirs('-H', p4path)

    p4subdir_names = [child['dir'] for child in p4subdirs]

    treeItem = idx.internalPointer()

    # print idx.child(0,0).data(), p4subidrs

    if not idx.child(0, 0).data() and p4subdirs:
        # Pop empty "None" child
        treeItem.popChild()

        for p4child in p4subdir_names:
            print p4child
            data = [os.path.basename(p4child), "Folder", "", "", ""]

            childData = TreeItem(data, treeItem)
            treeItem.appendChild(childData)

            childData.appendChild(None)

            files = p4Filelist(p4child, findDeleted)

            for f in files:
                fileName = os.path.basename(f['name'])
                data = [fileName, f['type'], f[
                    'time'], f['action'], f['change']]

                fileData = TreeItem(data, childData)
                childData.appendChild(fileData)


def tmp(*args):
    idx = args[0]

    children = []

    i = 1
    while True:
        child = idx.child(i, 0)
        print i, child.data()
        if not child.isValid():
            break

        children.append(child)
        i += 1

        populateSubDir(child, findDeleted=False)

    return

    treeItem = idx.internalPointer()

    idxPathModel = fullPath(idx, model.showDeleted)

    idxPathSubDirs = [idxPath.data() for idxPath in idxPathModel]
    idxFullPath = os.path.join(*idxPathSubDirs)
    pathDepth = len(idxPathSubDirs)

    children = []

    p4path = "//{0}/{1}/*".format(p4.client, idxFullPath)
    print p4path
    p4children = p4.run_dirs("-H", p4path)
    p4children_names = [child['dir'] for child in p4children]

    if idx.child(0, 0).data() == "TMP":
        for p4child in p4children_names:
            data = [p4child, "", "", ""]
            childData = TreeItem(data, idx)
            treeItem.appendChild(childData)

    i = 0
    while True:
        child = idx.child(i, 0)
        if not child.isValid():
            break

        children.append(child)
        i += 1

    for child in children:
        childIdx = child.internalPointer()

        data = ["TEST", "TEST", "TEST", "TEST"]
        childDir = TreeItem(data, childIdx)
        childIdx.appendChild(childDir)

        tmpDir = TreeItem(["TMP", "", "", "", ""], childDir)
        childDir.appendChild(tmpDir)

    # view.setModel(model)

view = QtGui.QTreeView()
view.expandAll()
view.setWindowTitle("Perforce Depot Files")
view.resize(512, 512)
view.expanded.connect(tmp)

model = TreeModel()
# model.populate("//{0}".format(p4.client), findDeleted=True)
model.populate("//depot", findDeleted=True)

view.setModel(model)

# populateSubDir( view.rootIndex() )

for i in range(model.rootrowcount()):
    idx = model.index(i, 0, model.parent(QtCore.QModelIndex()))

    treeItem = idx.internalPointer()

    populateSubDir(idx)

    # test = TreeItem( ["TEST", "", "", ""], treeItem  )
    # treeItem.appendChild( test )

view.setColumnWidth(0, 220)
view.setColumnWidth(1, 100)
view.setColumnWidth(2, 120)
view.setColumnWidth(3, 60)

view.show()
