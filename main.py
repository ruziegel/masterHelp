import sqlite3
import sys
import threading
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit, \
    QDialog, QDialogButtonBox, QLabel, QSpinBox, QCompleter, QInputDialog, QPlainTextEdit, QSizePolicy, QFileDialog, \
    QListWidget, QMessageBox

from PlayerWidget import ListPlayersWidget

DB_NAME = 'DNDDB.db'


class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.plist = ListPlayersWidget()
        self.sqlite_connection = sqlite3.connect(DB_NAME)
        # проверяет существующие таблицы в бд
        self.check_db()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle('Помощь мастеру')
        # система размещения всех элементов
        self.hboxmain = QHBoxLayout()
        self.vBox = QVBoxLayout()
        self.hboxplayersandturn = QHBoxLayout()
        self.vboxmenu = QVBoxLayout()
        self.hboxgame = QHBoxLayout()
        self.hboxtxtcsv = QHBoxLayout()

        self.addPlayersBut = QPushButton('Добавить игрока')
        self.addPlayersBut.clicked.connect(self.addPlayerClick)
        self.turnBut = QPushButton('ХОД')
        self.turnBut.clicked.connect(self.turn)
        self.newgamebut = QPushButton('Новый бой')
        self.newgamebut.clicked.connect(self.newgame)
        self.savegamebut = QPushButton('Сохранить игру')
        self.savegamebut.clicked.connect(self.savegame)
        self.loadgamebut = QPushButton('Загрузить игру')
        self.loadgamebut.clicked.connect(self.loadgame)
        self.txtbut = QPushButton('Просмотреть историю боя')
        self.txtbut.clicked.connect(self.savetxt)
        # размещаем все элементы
        self.setLayout(self.hboxmain)
        self.hboxmain.addLayout(self.vBox)
        self.hboxmain.addLayout(self.vboxmenu)
        self.vBox.addWidget(self.plist)
        self.vboxmenu.addLayout(self.hboxgame)
        self.vboxmenu.addLayout(self.hboxplayersandturn)
        self.vboxmenu.addLayout(self.hboxtxtcsv)
        self.hboxplayersandturn.addWidget(self.addPlayersBut)
        self.hboxplayersandturn.addWidget(self.turnBut)
        self.hboxgame.addWidget(self.newgamebut)
        self.hboxgame.addWidget(self.savegamebut)
        self.hboxgame.addWidget(self.loadgamebut)
        self.hboxtxtcsv.addWidget(self.txtbut)

        # test
        # for i in range(10):
        # self.addPlayer(name='гоблин'+str(i), init=randint(0, 20), hp=randint(1, 100))

    # обработчик нажатия кнопки Добавить игрока
    def addPlayerClick(self):
        name, init, hp, ok = AddPlayersWin.getValues()
        name = name.replace("'", "")
        name = name.replace('"', "")
        print(name, init, hp, ok)
        if ok:
            self.addPlayer(name=name, init=init, hp=hp)

    # Добавляет игрока
    def addPlayer(self, name=None, init=None, hp=None):
        print(name, init, hp)
        self.plist.add(name, init, hp)
        self.plist.listofplayerwidget[-1].deadbut.clicked.connect(self.dead)
        cur = self.sqlite_connection.cursor()
        # этот блок нужен для автозаполнения поля Имя при добавления игрока
        res = cur.execute("SELECT * from nicks "
                          "WHERE nick = '" + name + "'").fetchall()
        if len(res) == 0:
            cur.execute("INSERT INTO nicks(nick)"
                        "VALUES ( '" + name + "' )")
            self.sqlite_connection.commit()
        cur.close()

    # обработчик нажатия кнопки Ход
    def turn(self):
        self.plist.turn()

    # обработчик нажатия кнопки Новая игра
    def newgame(self):
        self.vBox.removeWidget(self.plist)
        self.plist = ListPlayersWidget()
        self.vBox.addWidget(self.plist)

    # обработчик нажатия кнопки Сохранить игру
    def savegame(self):
        text, ok = QInputDialog.getText(self, 'Сохранение игры',
                                        'Введите название игры',
                                        text=datetime.now().strftime("%d-%m-%Y %H-%M"))
        # защита от добавления кавычек в название игры
        text = text.replace("'", "")
        text = text.replace('"', "")
        if ok:
            print('Сохранить игру')
            gamename = text
            active = self.plist.active
            gameround = self.plist.active
            history = self.plist.strhistory()
            time = datetime.now().strftime("%Y-%m-%d %H-%M")
            cur = self.sqlite_connection.cursor()
            print(gamename, active, gameround, time)
            res = cur.execute('INSERT INTO games '
                              '(name, active, round, history, time) '''
                              'VALUES '
                              f'''("{gamename}", "{active}", "{gameround}", "{history}", "{time}")''')
            print(res.fetchall())
            self.sqlite_connection.commit()
            gameid = cur.lastrowid
            for pwidget in self.plist.listofplayerwidget:
                pname = pwidget.player.name
                hp = pwidget.player.hp
                init = pwidget.player.init
                cur.execute('INSERT INTO players '
                            '(name, hp, init, gameid) '
                            'VALUES '
                            f'("{pname}", "{hp}", "{init}", "{gameid}")')

            self.sqlite_connection.commit()
            cur.close()

    # обработчик нажатия кнопки Загрузить игру
    def loadgame(self):
        cur = self.sqlite_connection.cursor()
        self.model = cur.execute('SELECT g_id, name, time, active, round FROM games ORDER BY time DESC').fetchall()
        cur.close()
        if len(self.model) == 0:
            QMessageBox.about(self, "Ошибка", "Сохраненных игр нет")
        else:
            players, active, round, result = LoadGame.getGamePlayers()
            print(players, active, round, result)
            if result:
                self.newgame()
                for player in players:
                    self.addPlayer(name=player[0], hp=player[1], init=player[2])
                self.plist.active = active
                self.plist.round = round
                self.plist.update()

    # обработчик нажатия кнопки Просмотреть историю боя
    def savetxt(self):
        self.historywindow = ShowHistory(self.plist.history)
        self.historywindow.show()

    # обработчик нажатия кнопки Удалить игрока
    def dead(self):
        self.plist.remove(self.sender().parent())

    def check_db(self):
        cur = self.sqlite_connection.cursor()
        res = cur.execute('SELECT name FROM sqlite_master '
                          'WHERE type=\'table\''
                          ).fetchall()
        self.sqlite_connection.commit()
        res = [i[0] for i in res]
        print(res)
        res = cur.execute('CREATE TABLE IF NOT EXISTS nicks '
                          '(n_id INTEGER UNIQUE,'
                          'nick TEXT UNIQUE,'
                          'PRIMARY KEY(n_id AUTOINCREMENT))')
        self.sqlite_connection.commit()
        print(res.fetchall())
        res = cur.execute('CREATE TABLE IF NOT EXISTS players '
                          '(p_id INTEGER UNIQUE,'
                          'name TEXT,'
                          '"hp" INTEGER, '
                          'init INTEGER,'
                          '"gameid" INTEGER,'
                          'PRIMARY KEY(p_id AUTOINCREMENT))')
        self.sqlite_connection.commit()
        print(res.fetchall())
        res = cur.execute('CREATE TABLE IF NOT EXISTS games'
                          '(g_id INTEGER UNIQUE,'
                          'name TEXT,'
                          'active INTEGER,'
                          'round INTEGER,'
                          'history TEXT,'
                          'time TEXT,'
                          'PRIMARY KEY(g_id AUTOINCREMENT))')
        self.sqlite_connection.commit()
        print(res.fetchall())
        cur.close()

    def closeEvent(self, a0) -> None:
        self.sqlite_connection.commit()
        self.sqlite_connection.close()
        print('я закрылся')


class LoadGame(QDialog):
    def __init__(self, parent=None):
        super(LoadGame, self).__init__(parent)
        self.players = []
        self.activ = 0
        self.round = 0

        hmainlayout = QHBoxLayout(self)
        vbutslayout = QVBoxLayout(self)

        self.setLayout(hmainlayout)
        self.gamelist = QListWidget(self)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        hmainlayout.addWidget(self.gamelist)

        hmainlayout.addLayout(vbutslayout)
        vbutslayout.addWidget(buttons)

        self.sqlite_connection = sqlite3.connect(DB_NAME)
        cur = self.sqlite_connection.cursor()
        # получаем сохраненные игры для отображения
        self.model = cur.execute('SELECT g_id, name, time, active, round FROM games ORDER BY time DESC').fetchall()
        self.gamelist.addItems([i[1] + ' ' + i[2] for i in self.model])
        self.gamelist.itemClicked.connect(self.chooseitem)
        cur.close()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def chooseitem(self):
        print('Оппа! выбрали игру в строке', self.gamelist.currentRow())

    def values(self):
        print('пользователь выбрал строку', self.gamelist.currentRow())
        cur = self.sqlite_connection.cursor()
        print('Мы загружаем игру', self.model[self.gamelist.currentRow()])
        gameid = self.model[self.gamelist.currentRow()][0]
        active = self.model[self.gamelist.currentRow()][3]
        round = self.model[self.gamelist.currentRow()][4]
        res = cur.execute(f'SELECT name, hp, init FROM players WHERE gameid = {gameid}').fetchall()
        cur.close()
        return res, active, round

    @staticmethod
    def getGamePlayers(parent=None):
        dialog = LoadGame(parent)
        result = dialog.exec_()
        players, active, round = dialog.values()
        return players, active, round, result == QDialog.Accepted


class ShowHistory(QWidget):
    def __init__(self, content, parent=None):
        super(ShowHistory, self).__init__(parent)
        win = QPlainTextEdit()
        self.savebut = QPushButton('Сохранить')
        self.savebut.clicked.connect(self.savefiledialog)
        win.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content = '\n'.join(content)
        win.setPlainText(self.content)

        self.vmain = QVBoxLayout()
        self.setLayout(self.vmain)
        self.vmain.addWidget(win)
        self.vmain.addWidget(self.savebut)

    def savefiledialog(self):
        name, _ = QFileDialog.getSaveFileName(self,
                                              "Save File",
                                              f'{datetime.now().strftime("%d-%m-%Y %H-%M")}.txt',
                                              '.txt')
        thread = threading.Thread(target=self.multithreadsavefile, args=[name])
        thread.start()
        print('готовенько')

    # функция для записи в файл в другом потоке, чтобы окошко не "висло" если файл большой
    def multithreadsavefile(self, name):
        if name:
            with open(name, 'w') as ff:
                ff.write(self.content)
        print('Записал!')


class AddPlayersWin(QDialog):
    def __init__(self, parent=None):
        super(AddPlayersWin, self).__init__(parent)

        layout = QVBoxLayout(self)

        # мой виджет для добавления игрока
        nameLab = QLabel('Имя игрока')
        initLab = QLabel('Инициатива')
        hpLab = QLabel('Здоровье')

        self.name = QLineEdit()
        self.nicks = self.getnicks()
        completer = QCompleter(self.nicks, self.name)
        self.name.setCompleter(completer)
        self.init = QSpinBox()
        self.hp = QSpinBox()
        self.init.setRange(-20, 1000)
        self.hp.setRange(-20, 1000)

        hBoxLayout1 = QHBoxLayout()
        hBoxLayout2 = QHBoxLayout()
        hBoxLayout3 = QHBoxLayout()

        hBoxLayout1.addWidget(nameLab)
        hBoxLayout1.addWidget(self.name)
        hBoxLayout2.addWidget(initLab)
        hBoxLayout2.addWidget(self.init)
        hBoxLayout3.addWidget(hpLab)
        hBoxLayout3.addWidget(self.hp)
        layout.addLayout(hBoxLayout1)
        layout.addLayout(hBoxLayout2)
        layout.addLayout(hBoxLayout3)

        # кнопочки ок и отмена
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # получаем значения из полей
    def values(self):
        return self.name.text(), self.init.text(), self.hp.text()

    def getnicks(self):
        self.sqlite_connection = sqlite3.connect(DB_NAME)
        cur = self.sqlite_connection.cursor()
        res = [i[0] for i in cur.execute("SELECT nick FROM nicks").fetchall()]
        self.sqlite_connection.commit()
        print(res)
        cur.close()
        self.sqlite_connection.close()
        return res

    # статичный метод для создания диалога и возвращения значений
    @staticmethod
    def getValues(parent=None):
        dialog = AddPlayersWin(parent)
        result = dialog.exec_()
        name, init, hp = dialog.values()
        return name, init, hp, result == QDialog.Accepted


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
