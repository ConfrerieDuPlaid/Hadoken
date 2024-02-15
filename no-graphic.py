import sys

from logic import *


class Environment(LogicEnvironment):
    def __init__(self, learning_rate, discount_factor):
        super().__init__(learning_rate, discount_factor)
        self.agents = {
            RYU: Agent(self, RYU, learning_rate, discount_factor),
            KEN: Agent(self, KEN, learning_rate, discount_factor),
        }
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def print_map(self):
        for i in range(GRID_LIMIT):
            if i == self.LEFT_WALL or i == self.RIGHT_WALL:
                print('|', end='')
            elif self.positions[RYU] == i and self.positions[KEN] == i:
                print('O', end='')
            elif self.positions[RYU] == i:
                print('R', end='')
            elif self.positions[KEN] == i:
                print('K', end='')
            else:
                print('_', end='')
        print()


class Agent(LogicAgent):
    def __init__(self, environment, player_name, learning_rate, discount_factor):
        super().__init__(environment, player_name, learning_rate, discount_factor)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor


class NonGraphic(Game):
    def __init__(self, learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR):
        super().__init__(learning_rate, discount_factor)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def setup(self):
        self.env = Environment(self.learning_rate, self.discount_factor)

        self.Ken = self.env.agents[KEN]
        # self.Ken.load_qtable("KenQtable.qtable")

        self.Ryu = self.env.agents[RYU]
        # self.Ryu.load_qtable("RyuQtable.qtable")

    def run(self):
        while self.wins < self.max_wins and not self.exit_game:
            self.round()
            self.check_end_game()
            if self.Ken.get_score() < -35000 or self.Ryu.get_score() < -35000:
                self.end_game()
                exit(0)
            if self.wins >= self.max_wins:
                self.end_game()
                exit(0)


if __name__ == '__main__':
    window = NonGraphic(learning_rate=float(sys.argv[1]) / 100.0,
                     discount_factor=float(sys.argv[2]) / 100.0)
    window.setup()
    window.run()
