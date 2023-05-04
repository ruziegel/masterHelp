class Player:  # класс описывает одного игрока в игре
    def __init__(self, name, init, hp):
        self.name = name
        self.init = init
        self.hp = hp

    def __str__(self):
        return self.name + ' ' + str(self.init) + ' ' + str(self.hp)
