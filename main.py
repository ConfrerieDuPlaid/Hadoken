import pickle
import sys
from os.path import exists

from matplotlib import pyplot as plt
from random import random, choice

RYU = "Ryu"
KEN = "Ken"
PLAYERS = [RYU, KEN]

ACTION_LEFT, ACTION_RIGHT, ACTION_JUMP, ACTION_CROUCH, ACTION_DODGE, ACTION_NONE = 'L', 'R', 'J', 'C', 'D', 'N'
ACTION_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK = 'P', 'LK', 'HK'
ACTIONS = [ACTION_LEFT, ACTION_RIGHT, ACTION_JUMP, ACTION_CROUCH, ACTION_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_DODGE, ACTION_NONE]
ATTACKS = [ACTION_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK]  # todo add jump and crouch to actions

ORIENTATION_LEFT, ORIENTATION_RIGHT = -1, 1
ORIENTATIONS = [ORIENTATION_RIGHT, ORIENTATION_LEFT]
MOVES = {
    ACTION_LEFT: (-1, ORIENTATION_LEFT),
    ACTION_RIGHT: (1, ORIENTATION_RIGHT),
}

REWARD_WIN = 100
REWARD_LOSE = -200
REWARD_WALL = -2
REWARD_HIT = 10
REWARD_GET_HIT = -20
REWARD_DODGE = 12
REWARD_MOVE = -1
REWARD_NONE = -1
HIT_DAMAGE = 10

DISTANCE_NONE, DISTANCE_NEAR, DISTANCE_MID, DISTANCE_FAR = '0', 'N', 'M', 'F'
DISTANCES = {
    DISTANCE_NONE: 0,
    DISTANCE_NEAR: 1,
    DISTANCE_MID: 2,
    DISTANCE_FAR: 3,
}

STANCE_STANDING, STANCE_CROUCHING, STANCE_JUMPING = 'S', 'C', 'J'
STANCES = [STANCE_STANDING, STANCE_CROUCHING, STANCE_JUMPING]
STANCE_HIT_MAP = {
    STANCE_JUMPING: {
        STANCE_JUMPING: [ACTION_PUNCH],
        STANCE_STANDING: [ACTION_LOW_KICK],
        STANCE_CROUCHING: [],
    },
    STANCE_STANDING: {
        STANCE_JUMPING: [ACTION_HIGH_KICK],
        STANCE_STANDING: [ACTION_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK],
        STANCE_CROUCHING: [ACTION_LOW_KICK],
    },
    STANCE_CROUCHING: {
        STANCE_JUMPING: [],
        STANCE_STANDING: [ACTION_HIGH_KICK, ACTION_PUNCH],
        STANCE_CROUCHING: [ACTION_PUNCH, ACTION_LOW_KICK],
    },
}
STANCE_CHANGES = {
    ACTION_JUMP: STANCE_JUMPING,
    ACTION_CROUCH: STANCE_CROUCHING,
}

WALL = '#'
GRID_LIMIT = 10
KEN_START = 2
RYU_START = 6


def distance_to_range(distance):
    if distance == 0:
        return DISTANCE_NONE
    elif distance == 1:
        return DISTANCE_NEAR
    elif distance == 2:
        return DISTANCE_MID
    else:
        return DISTANCE_FAR


def arg_max(table):
    return max(table, key=table.get)


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


class Environment:
    LEFT_WALL = 0
    RIGHT_WALL = GRID_LIMIT - 1

    def __init__(self):
        self.positions = {
            RYU: RYU_START,
            KEN: KEN_START,
        }
        self.orientations = {
            RYU: ORIENTATION_RIGHT,
            KEN: ORIENTATION_LEFT,
        }
        self.stances = {
            RYU: STANCE_STANDING,
            KEN: STANCE_STANDING,
        }
        self.radars = {
            RYU: self.get_radar(RYU),
            KEN: self.get_radar(KEN),
        }
        self.agents = {
            RYU: {},
            KEN: {},
        }

    def reset(self):
        self.positions = {
            KEN: KEN_START,
            RYU: RYU_START,
        }
        self.orientations = {
            RYU: ORIENTATION_RIGHT,
            KEN: ORIENTATION_LEFT,
        }
        self.stances = {
            RYU: STANCE_STANDING,
            KEN: STANCE_STANDING,
        }
        self.radars = {
            RYU: self.get_radar(RYU),
            KEN: self.get_radar(KEN),
        }

    def set_agents(self, ryu, ken):
        self.agents[RYU] = ryu
        self.agents[KEN] = ken

    @staticmethod
    def opponent(player):
        if player == KEN:
            return RYU
        return KEN

    def get_radar(self, player):
        radar = ['_'] * 9
        radar[7] = self.orientations[player]
        radar[8] = self.stances[player]
        opponent = self.opponent(player)
        player_position = self.positions[player]
        distance_opponent = self.distance_between_players()
        orientation_to_opponent = -sign(player_position - self.positions[opponent])
        range_left_wall = distance_to_range(player_position)
        range_right_wall = distance_to_range(self.RIGHT_WALL - player_position)
        radar[3 - DISTANCES[range_left_wall]] = WALL
        radar[3 + DISTANCES[range_right_wall]] = WALL
        radar[3 + orientation_to_opponent * DISTANCES[distance_opponent]] = self.stances[opponent]
        return tuple(radar)

    def distance_between_players(self):
        return distance_to_range(abs(self.positions[RYU] - self.positions[KEN]))

    def player_move(self, player, move):
        radar = self.get_radar(player)
        move_delta, self.orientations[player] = MOVES[move]
        self.agents[player].orientation = self.orientations[player]
        if radar[3 + move_delta] == WALL:
            return REWARD_WALL
        self.positions[player] += move_delta
        return REWARD_MOVE

    def is_within_range(self, attacker, attack):
        player_stance = self.stances[attacker]
        opponent_stance = self.stances[self.opponent(attacker)]
        if attack not in STANCE_HIT_MAP[player_stance][opponent_stance]:
            return False
        radar = self.get_radar(attacker)
        target = radar[3 + self.orientations[attacker]]
        return target != WALL and target != '_'  # todo not = self

    def reset_player_stance(self, player):
        if self.stances == STANCE_STANDING:
            return
        previous_action = self.agents[player].previous_actions[1]
        if previous_action == ACTION_JUMP or previous_action == ACTION_CROUCH:
            self.stances[player] = STANCE_STANDING

    def do(self, player):
        reward = 0
        opponent = self.opponent(player)
        last_opponent_action = self.agents[opponent].current_action
        damage_inflicted = False
        self.reset_player_stance(player)
        action = self.agents[player].current_action
        if action in MOVES:
            was_within_range = self.is_within_range(opponent, last_opponent_action)
            reward += self.player_move(player, action)
            if was_within_range:
                reward += REWARD_DODGE

        if action in STANCE_CHANGES:
            was_within_range = self.is_within_range(opponent, last_opponent_action)
            self.stances[player] = STANCE_CHANGES[action]
            reward = REWARD_MOVE
            is_within_range = self.is_within_range(player, last_opponent_action)
            if was_within_range and is_within_range:
                reward += REWARD_DODGE

        if action in ATTACKS:
            if self.is_within_range(player, action):
                # if last_opponent_action == ACTION_DODGE:
                #     reward -= REWARD_HIT
                # else:
                reward += REWARD_HIT
                damage_inflicted = True
            else:
                reward -= REWARD_HIT

        if action == ACTION_DODGE:
            if last_opponent_action in ATTACKS and self.is_within_range(opponent, last_opponent_action):
                reward += REWARD_DODGE
            else:
                reward -= REWARD_DODGE

        if action == ACTION_NONE:
            reward += REWARD_NONE

        if damage_inflicted:
            self.inflict_damage_to(self.opponent(player))

        return reward, self.get_radar(player)

    def inflict_damage_to(self, opponent):
        self.agents[opponent].get_hit()

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


class Agent:
    def __init__(self, environment, player_name, default_orientation=1, learning_rate=0.50, discount_factor=0.70, noise = 0.4):
        super().__init__()
        self.cur_texture = 0
        self.noise = noise
        self.orientation = environment.orientations[player_name]
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.env = environment
        self.state = (
        environment.radars[player_name], environment.orientations[player_name], environment.stances[player_name])
        self.stance = STANCE_STANDING
        self.previous_state = self.state
        self.previous_actions = [ACTION_NONE, ACTION_NONE, ACTION_NONE]
        self.current_action = ACTION_NONE
        self.player_name = player_name
        self.health = 100
        self.qtable = {}
        self.score = 0
        self.current_animation = 0
        self.animations = []

    def load_qtable(self, filename):
        if exists(filename):
            with open(filename, 'rb') as file:
                self.qtable = pickle.load(file)
            self.reset()

    def facing(self):
        return self.orientation == ORIENTATION_LEFT

    def reset(self):
        self.orientation = self.env.orientations[self.player_name]
        self.state = self.env.radars[self.player_name]
        self.health = 100
        self.score = 0

    def choose_action(self):
        if random() < self.noise:
            self.current_action = choice(ACTIONS)
            return
        self.add_qtable_state(self.state)
        self.current_action = arg_max(self.qtable[self.state])

    def add_qtable_state(self, state):
        if state not in self.qtable.keys():
            self.qtable[state] = {}
            for a in ACTIONS:
                self.qtable[state][a] = 0.0

    def update_qtable(self, reward, prev_state, new_state):
        self.add_qtable_state(prev_state)
        self.add_qtable_state(new_state)
        max_q = max(self.qtable[new_state].values())
        self.qtable[prev_state][self.previous_actions[0]] += self.learning_rate * (
                reward + self.discount_factor * max_q - self.qtable[prev_state][self.current_action])

    def do(self):
        self.choose_action()
        reward, new_state = self.env.do(self.player_name)
        self.score += reward

        self.update_qtable(reward, self.state, new_state)
        self.previous_state = self.state
        self.push_previous_action()
        self.state = new_state
        return self.current_action

    def push_previous_action(self):
        self.previous_actions.pop()
        self.previous_actions.insert(0, self.current_action)

    def get_state(self):
        return f"{self.previous_state} {self.qtable[self.previous_state]}"

    def get_hit(self):
        self.health -= HIT_DAMAGE

    def is_dead(self):
        return self.health <= 0

    def get_health(self):
        return self.health

    def get_score(self):
        return self.score

    def win(self):
        self.score += REWARD_WIN
        self.update_qtable(REWARD_WIN, self.previous_state, self.state)

    def lose(self):
        self.score += REWARD_LOSE
        self.update_qtable(REWARD_LOSE, self.previous_state, self.state)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.qtable, file)


class NonGraphic:
    def __init__(self, learning_rate=0.5, discount_factor=0.5, noise=0.5):
        self.player_list = None
        self.max_wins = 500
        self.ryu_wins = 0
        self.ken_wins = 0
        self.wins = 0
        self.iterations = 0
        self.ken_score = []
        self.ryu_score = []
        self.Ryu = None
        self.Ken = None
        self.env = None
        self.gui_camera = None
        self.camera = None
        self.scene = None
        self.wall_list = None
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.noise = noise
        self.exit_game = False

    def setup(self):
        self.env = Environment()

        self.Ken = Agent(self.env, KEN, learning_rate=self.learning_rate, discount_factor=self.discount_factor,
                         noise=self.noise)
        # self.Ken.load_qtable("KenQtable.qtable")

        self.Ryu = Agent(self.env, RYU, learning_rate=self.learning_rate, discount_factor=self.discount_factor,
                         noise=self.noise)
        # self.Ryu.load_qtable("RyuQtable.qtable")

        self.env.set_agents(self.Ryu, self.Ken)

    def run(self):
        while self.wins < self.max_wins and not self.exit_game:
            self.update()
            if self.Ryu.is_dead() or self.Ken.is_dead():
                if self.Ryu.is_dead():
                    self.Ryu.lose()
                    self.Ken.win()
                    self.ken_wins += 1
                    # self.display_victory(KEN)
                else:
                    self.Ryu.win()
                    self.Ken.lose()
                    self.ryu_wins += 1
                    # self.display_victory(RYU)
                self.env.reset()
                self.ken_score.append(self.Ken.get_score())
                self.ryu_score.append(self.Ryu.get_score())
                self.Ryu.reset()
                self.Ken.reset()
                self.wins += 1
                # print(self.ken_wins + self.ryu_wins)
            if self.Ken.get_score() < -35000 or self.Ryu.get_score() < -35000:
                self.end_game()
                exit(0)
            if self.wins >= self.max_wins:
                self.end_game()
                exit(0)

    def update(self):
        player_start = choice(PLAYERS)
        if player_start == RYU:
            self.Ryu.do()
        else:
            self.Ken.do()
        self.iterations += 1

    def end_game(self):
        # self.wins = self.max_wins
        self.env.reset()
        plt.plot(self.ryu_score, label="Ryu")
        plt.plot(self.ken_score, label="Ken")
        # self.Ryu.save("RyuQtable.qtable")
        # self.Ken.save("KenQtable.qtable")
        # print(f"Ryu wins: {self.ryu_wins}, Ken wins: {self.ken_wins}")
        if self.wins > 100:
            plt.legend()
            plt.savefig(f"graphs/{self.wins}_{self.learning_rate}_d_{self.discount_factor}_n_{self.noise}.png")
            self.exit_game = True


if __name__ == '__main__':
    window = NonGraphic(learning_rate=float(sys.argv[1]) / 100.0,
                     discount_factor=float(sys.argv[2]) / 100.0,
                     noise=float(sys.argv[3]) / 100.0)
    window.setup()
    window.run()
