import json
import codecs
import os
import glob

import sys
from PyQt5.QtWidgets import (QWidget, QToolTip,
    QPushButton, QApplication, QMessageBox, QGridLayout, QFileDialog)
from PyQt5.QtCore import QCoreApplication
import UtakoCore as core
import UtakoAnalyzer as analyzer

class UtakoMain(QWidget):

    def __init__(self):
        super().__init__()

        btnGetNewest = QPushButton('最新動画を取得', self)
        btnGetNewest.clicked.connect(self.rankreq)

        btnNewTeacher = QPushButton('新しい教師データの作成',self)
        btnNewTeacher.clicked.connect(self.newTeacher)

        btnPerceptron = QPushButton('学習実行',self)
        btnPerceptron.clicked.connect(self.Perceptron)

        btnAll = QPushButton('一括作業',self)
        btnAll.clicked.connect(self.alldo)

        btnQuit = QPushButton('とじる',self)
        btnQuit.clicked.connect(QCoreApplication.instance().quit)

        layout = QGridLayout()
        layout.addWidget(btnGetNewest,0,0)
        layout.addWidget(btnNewTeacher,1,0)
        layout.addWidget(btnPerceptron,2,0)
        layout.addWidget(btnAll,3,0)
        layout.addWidget(btnQuit,4,0)

        self.setGeometry(300, 300, 300, 275)
        self.setWindowTitle('U.Orihara')
        self.setLayout(layout)

    def alldo(self):
        self.rankreq()
        self.newTeacher()
        self.Perceptron()

    def rankreq(self):
        UtakoCore.rankreq(GUI = True)

    def newTeacher(self):
        UtakoCore.teach(GUI = True)

    def Perceptron(self):
        miss = UtakoCore.Perceptron(GUI = True)
        if miss == 0:
            QMessageBox.information(self,"学習完了","今回のデータは全問正解よ。")
        else:
            QMessageBox.information(self,"学習完了","勉強してきたわ。" + str(miss) + "回くらい予測ミスしたけどその分強くなったわ。")

if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainWindow = UtakoMain()
    mainWindow.show()
    sys.exit(app.exec_())
