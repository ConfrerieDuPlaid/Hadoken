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
    def __init__(self, learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR,
                 qtable_suffix="", load_qtables=True):
        super().__init__(learning_rate, discount_factor)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.qtable_suffix = qtable_suffix
        self.load_qtables = load_qtables

    def setup(self):
        self.env = Environment(self.learning_rate, self.discount_factor)

        self.Ken = self.env.agents[KEN]
        self.Ryu = self.env.agents[RYU]
        if self.load_qtables:
            self.Ken.load_qtable(self.qtable_path(KEN))
            self.Ryu.load_qtable(self.qtable_path(RYU))

    def run(self):
        try:
            while self.wins < self.max_wins and not self.exit_game:
                self.round()
                self.check_end_game()
                if self.Ken.get_score() < -35000 or self.Ryu.get_score() < -35000:
                    self.end_game()
                    exit(0)
                if self.wins >= self.max_wins:
                    self.end_game()
                    exit(0)
        except KeyboardInterrupt:
            # Ctrl+C : on sauvegarde l'apprentissage avant de quitter
            self.end_game()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        # Lancé par launch.py : chaque couple d'hyperparamètres apprend de zéro
        # et enregistre ses Q-tables dans ses propres fichiers.
        learning_rate = float(sys.argv[1]) / 100.0
        discount_factor = float(sys.argv[2]) / 100.0
        window = NonGraphic(learning_rate, discount_factor,
                            qtable_suffix=f"_l_{learning_rate}_d_{discount_factor}",
                            load_qtables=False)
    else:
        # Sans argument : reprend et enrichit les mêmes Q-tables que le mode graphique
        window = NonGraphic()
    window.setup()
    window.run()
