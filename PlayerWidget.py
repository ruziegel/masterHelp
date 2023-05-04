import os
import sys
from datetime import datetime

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox

from PlayerModel import Player


# этот блок изменяет пути файлов чтобы картинки при упаковке добавлялись в исполняемый файл
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# класс представляет из себя одну карточку игрока
class PlayerWidget(QWidget):
    def __init__(self, player, parent=None):
        QWidget.__init__(self, parent=parent)
        self.player = player
        self.initUI()

    def initUI(self):
        style = 'border-style: solid; border-width: 1px; border-color: black;'
        self.labelNum = QLabel('1.', self)
        self.labelNum.setStyleSheet(style)
        self.labelName = QLabel(self.player.name, self)
        self.labelName.setStyleSheet(style)
        self.deadbut = QPushButton(self)
        self.deadbut.setIcon(QIcon(resource_path('skull.png')))
        self.labelInit = QLabel('Инициатива: ' + str(self.player.init), self)
        self.labelInit.setStyleSheet(style)
        self.hpbox = QSpinBox()
        self.hpbox.setRange(-2147483648, 2147483647)
        self.hpbox.valueChanged.connect(self.changehp)
        self.hpbox.setValue(int(self.player.hp))

        vBoxLeft = QVBoxLayout()
        h2BoxNumName = QHBoxLayout()
        hBoxInitHp = QHBoxLayout()
        h2BoxNumName.addWidget(self.labelNum)
        h2BoxNumName.addWidget(self.labelName)
        h2BoxNumName.addWidget(self.deadbut)
        vBoxLeft.addLayout(h2BoxNumName)
        hBoxInitHp.addWidget(self.labelInit)
        hBoxInitHp.addWidget(self.hpbox)
        vBoxLeft.addLayout(hBoxInitHp)
        self.setLayout(vBoxLeft)
        self.setFixedHeight(70)
        self.setStyleSheet(style)

    # применяется для отладки
    def __str__(self):
        return str(type(self)) + ' ' + self.player.name

    # применяется для отладки
    def __repr__(self):
        return str(type(self)) + ' ' + self.player.name

    # когда здоровье игрока падает до нуля его карточка подсвечивается красным
    def changehp(self):
        self.player.hp = self.hpbox.value()
        if self.player.hp <= 0:
            self.setStyleSheet('background-color: red;')
        else:
            self.setStyleSheet('background-color: white;')


# Класс описывает одну игровую сессию и взаимодействие карточек игрока
class ListPlayersWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.round = 1
        self.labelRound = QLabel('Раунд ' + str(self.round), self)
        self.listofplayerwidget = []
        self.active = 0
        self.oldhp = {}
        self.newhp = {}
        self.history = []
        self.initUI()

    def initUI(self):
        self.vBoxMain = QVBoxLayout()
        self.vBoxMain.addWidget(self.labelRound)
        self.setLayout(self.vBoxMain)

    def add(self, name, init, hp):
        newplayer = Player(name, init, hp)
        self.history.append(f'{datetime.now().strftime("%d-%m-%Y %H:%M")} Добавлен игрок {name} с инициативой {init} и здоровьем {hp}')
        self.oldhp[name] = hp
        newwidget = PlayerWidget(player=newplayer)
        self.listofplayerwidget.append(newwidget)
        self.listofplayerwidget.sort(key=lambda x: int(x.player.init), reverse=True)
        self.update()

    def turn(self):
        self.active += 1
        if self.active >= len(self.listofplayerwidget):
            self.active = 0
            self.newhp.clear()
            self.history.append(f'{datetime.now().strftime("%d-%m-%Y %H:%M")} Раунд {self.round}')
            for i in self.listofplayerwidget:
                self.newhp[i.player.name] = i.player.hp
            for i in self.newhp.keys():
                print(i)
                new = self.newhp[i]
                print(new)
                old = self.oldhp[i]
                print(old)
                if new != old:
                    self.history.append(f'{datetime.now().strftime("%d-%m-%Y %H:%M")} Здоровье игрока {i} изменено с {old} на {new}')
            self.oldhp = self.newhp.copy()
            self.round += 1
        self.update()

    def strhistory(self):
        return '\n'.join(self.history)

    def remove(self, widget):
        print(self.listofplayerwidget)
        if self.active <= self.listofplayerwidget.index(widget) and self.active != 0:
            self.active -= 1
        self.vBoxMain.removeWidget(widget)
        self.listofplayerwidget.remove(widget)
        print(self.listofplayerwidget)
        self.update()

    def update(self) -> None:
        self.labelRound.setText('Раунд ' + str(self.round))
        counter = self.active
        for i in range(len(self.listofplayerwidget)):
            self.listofplayerwidget[counter].labelNum.setText(str(i + 1) + '.')
            self.vBoxMain.insertWidget(i + 1, self.listofplayerwidget[counter])
            counter += 1
            if counter >= len(self.listofplayerwidget):
                counter = 0
