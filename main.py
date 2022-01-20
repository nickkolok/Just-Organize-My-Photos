from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog
from PyQt5.QtGui import QPixmap
from datetime import datetime
import os, sys, glob, math, subprocess
from PyQt5 import QtCore
from PIL import Image
from math import floor, log, pow
from ui import *

def convert_size(size_bytes):
   if size_bytes == 0: return "0"
   i = int(floor(log(size_bytes, 1024)))
   s = round(size_bytes / pow(1024, i), 2)
   return f"{s} {('B','KB','MB','GB')[i]}"

def getModifyDate(path):
    ts = os.path.getmtime(path)
    return "Null" if ts < 0 else datetime.fromtimestamp(ts).strftime('%d.%m.%Y')

class Ui(QMainWindow):
    #TODO: вынести код в удобные красивые функции
    #TODO: реализовать алгоритм выбора папки для шортката
    #TODO: пофиксить баг с невозможностью перемещения в корзину

    def __init__(self):
        # variables
        self.image_id   = 0
        self.im_count   = 0
        self.image_list = []
        self.path       = ""
        self.image_path = ""
        self.image      = None
        
        super(Ui, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setChildrenFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.path_btn.clicked.connect(self.checkPath)
        self.ui.btn_next.clicked.connect(self.nextImage)
        self.ui.btn_prev.clicked.connect(self.prevImage)
        self.ui.btn_del.clicked.connect(self.deleteImage)
        self.ui.graphicsView.setMouseTracking(True)
        self.ui.graphicsView.viewport().installEventFilter(self)
        self.show()

    def nextImage(self): self.changeImage(1)
    def prevImage(self): self.changeImage(-1)

    def viewImage(self):
        if self.image_path != "":
            os.startfile(self.image_path, 'open')

    def showImageInExplorer(self):
        if self.image_path != "":
            subprocess.run([
                os.path.join(os.getenv('WINDIR'), 'explorer.exe'),
                '/select,',
                os.path.normpath(self.image_path)])

    def setChildrenFocusPolicy(self, policy):
        def recursiveSetChildFocusPolicy (parentQWidget):
            for childQWidget in parentQWidget.findChildren(QtWidgets.QWidget):
                childQWidget.setFocusPolicy(policy)
                recursiveSetChildFocusPolicy(childQWidget)
        recursiveSetChildFocusPolicy(self.ui.centralwidget)

    def pickDirectory(self):
        return str(QFileDialog.getExistingDirectory(self, "Select Directory"))
    
    def checkPath(self): # currently not supporting RAW, ARW, ...
        temp = self.pickDirectory()
        if temp != "":
            self.path = temp
            self.image_list = [item.replace("\\", "/") for i in [glob.glob(f"{self.path}/*{ext}") for ext in ["jpg","jpeg","png"]] for item in i]
            self.im_count = len(self.image_list)
            self.image_id = 0
            self.ui.path_text.setText(f"path: {self.path} ({self.im_count} photo)")
            if self.im_count > 0:
                self.displayImg()
    
    def deleteImage(self):
        del_img = self.image_list.pop(self.image_id)
        # QtCore.QFile.moveToTrash(del_img)
        os.remove(del_img) # временное решение
        self.im_count = len(self.image_list)
        if self.image_id == self.im_count: self.image_id -= 1
        self.displayImg()

    def displayImg(self):
        if self.im_count > 0:
            self.image_path = self.image_list[self.image_id]
            if os.path.isfile(self.image_path):
                w, h = self.ui.graphicsView.width(), self.ui.graphicsView.height()
                scene = QtWidgets.QGraphicsScene(self)
                pixmap = QPixmap(self.image_path)
                item = QtWidgets.QGraphicsPixmapItem(pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio))
                scene.addItem(item)
                self.ui.graphicsView.setScene(scene)
                self.ui.path_text.setText(f"File: {os.path.basename(self.image_path)}\nPath: {self.path}")
                
                try:
                    self.image = Image.open(self.image_path)
                    self.ui.info_text.setText(
                        f"Image {self.image_id + 1} / {self.im_count}\n" +
                        f"Res: {' × '.join([str(i) for i in self.image.size])}\n" +
                        f"Size: {convert_size(os.path.getsize(self.image_path))}\n" +
                        f"Date: {getModifyDate(self.image_path)}") # full: %d.%m.%Y %H:%M:%S
                except OSError:
                    print("что-то пошло по пизде") # debug
                    self.ui.info_text.setText(
                        f"Image {self.image_id + 1} / {self.im_count}\nRes: Null\n" +
                        f"Size: {convert_size(os.path.getsize(self.image_path))}\nDate: Null\n" +
                        "[ corrupted image file ]")

    # def mousePressEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         print("Press!")

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.viewImage()
            elif event.button() == QtCore.Qt.RightButton:
                self.showImageInExplorer()
        return super(Ui, self).eventFilter(source, event)

    def changeImage(self, order):
        self.image_id += order
        if self.image_id == self.im_count:
            self.image_id = 0
        elif self.image_id < 0:
            self.image_id = self.im_count-1
        self.displayImg()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_1:
            self.changeImage(1) # for test
        elif event.key() == QtCore.Qt.Key_2:
            self.changeImage(-1) # for test
        elif event.key() == QtCore.Qt.Key_Right:
            self.changeImage(1)
        elif event.key() == QtCore.Qt.Key_Left:
            self.changeImage(-1)
        # elif event.key() == QtCore.Qt.Key_Delete:
        # elif event.key() == QtCore.Qt.Key_0:
        # elif event.key() == QtCore.Qt.Key_Enter:
        # elif event.key() == QtCore.Qt.Key_Space:
        else:
            QMainWindow.keyPressEvent(self, event)

# run app
app, ui = QApplication([]), Ui()
sys.exit(app.exec_())


## жалкие попытки перемещать файл в корзину ##

# def deleteImage(self):
#     im_pth = self.image_list.pop(self.image_id)
#     self.im_count = len(self.image_list)
#     # print(im_pth)
#     # print(os.path.realpath(im_pth))
#     file = QFile(im_pth)
#     send2trash(str(file.fileName()).replace("/", "\\"))
#     file.close()
#     # print(file.moveToTrash())
#     # print(file.fileName())
#     # send2trash(os.path.realpath(im_pth))
#     # QFile.moveToTrash(os.path.realpath(im_pth))
#     if self.image_id == self.im_count:
#         self.image_id -= 1
#     self.displayImg()

# from send2trash import send2trash
# QtCore.QFile.moveToTrash("D:/Projects/PhotoOrganizer/test_for_del/20210629_193404.jpg")
# send2trash(os.path.abspath("D:/Projects/PhotoOrganizer/test_for_del/f65240960.jpeg"))
# def deleteFile(path): QtCore.QFile.moveToTrash(QtCore.QFile(path))