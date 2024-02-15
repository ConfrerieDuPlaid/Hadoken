import pickle
from os.path import exists

from matplotlib import pyplot as plt
from random import random, choice

LEARNING_RATE = 0.6
DISCOUNT_FACTOR = 0.25
NOISE = 0.2
MAX_WIN = 10_000

RYU = "Ryu"
KEN = "Ken"
PLAYERS = [RYU, KEN]

ACTION_LEFT, ACTION_RIGHT, ACTION_JUMP, ACTION_CROUCH, ACTION_DODGE, ACTION_NONE = 'L', 'R', 'J', 'C', 'D', 'N'
ACTION_PUNCH, ACTION_HIGH_PUNCH, ACTION_LOW_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK = 'P', 'HP', 'LP', 'LK', 'HK'
ACTIONS = [ACTION_NONE, ACTION_DODGE, ACTION_JUMP, ACTION_CROUCH, ACTION_PUNCH,
           # ACTION_HIGH_PUNCH, ACTION_LOW_PUNCH,
           ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LEFT, ACTION_RIGHT]
ATTACKS = [ACTION_PUNCH, ACTION_HIGH_PUNCH, ACTION_LOW_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK]

ORIENTATION_LEFT, ORIENTATION_RIGHT = -1, 1
ORIENTATIONS = [ORIENTATION_RIGHT, ORIENTATION_LEFT]
MOVES = {
    ACTION_LEFT: (-1, ORIENTATION_LEFT),
    ACTION_RIGHT: (1, ORIENTATION_RIGHT),
}

REWARD_WIN = 1000
REWARD_COMBO = 500
REWARD_WALL = -2
REWARD_HIT = 100
REWARD_GET_HIT = -20
REWARD_MOVE = -2
REWARD_NONE = -2
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
        STANCE_STANDING: [ACTION_LOW_KICK, ACTION_LOW_PUNCH],
        STANCE_CROUCHING: [],
    },
    STANCE_STANDING: {
        STANCE_JUMPING: [ACTION_HIGH_KICK, ACTION_HIGH_PUNCH],
        STANCE_STANDING: [ACTION_PUNCH, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_HIGH_PUNCH, ACTION_LOW_PUNCH],
        STANCE_CROUCHING: [ACTION_LOW_KICK, ACTION_LOW_PUNCH],
    },
    STANCE_CROUCHING: {
        STANCE_JUMPING: [],
        STANCE_STANDING: [ACTION_HIGH_KICK, ACTION_HIGH_PUNCH],
        STANCE_CROUCHING: [ACTION_PUNCH],
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


class LogicEnvironment:
    LEFT_WALL = 0
    RIGHT_WALL = GRID_LIMIT - 1

    def __init__(self, learning_rate, discount_factor):
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
            RYU: tuple([]),
            KEN: tuple([]),
        }
        self.agents = {
            RYU: LogicAgent(self, RYU, learning_rate, discount_factor),
            KEN: LogicAgent(self, KEN, learning_rate, discount_factor),
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
        self.agents[KEN].reset()
        self.agents[RYU].reset()

    @staticmethod
    def opponent(player):
        if player == KEN:
            return RYU
        return KEN

    def get_radar(self, player):
        radar = ['_'] * 15
        radar[7] = self.orientations[player]
        radar[8] = self.stances[player]
        opponent = self.opponent(player)
        player_position = self.positions[player]
        distance_opponent = self.distance_between_players()
        orientation_to_opponent = sign(self.positions[opponent] - player_position)
        range_left_wall = distance_to_range(player_position)
        range_right_wall = distance_to_range(self.RIGHT_WALL - player_position)
        radar[3 - DISTANCES[range_left_wall]] = WALL  # todo refacto ?
        radar[3 + DISTANCES[range_right_wall]] = WALL
        radar[3 + orientation_to_opponent * DISTANCES[distance_opponent]] = self.stances[opponent]
        for i in range(3):
            radar[9 + i] = self.opponent_previous_actions(player)[i]
        for i in range(3):
            radar[12 + i] = self.agents[player].previous_actions[i]
        return tuple(radar)

    def distance_between_players(self):
        return distance_to_range(abs(self.positions[RYU] - self.positions[KEN]))

    def player_move(self, player, move):
        radar = self.get_radar(player)
        move_delta, self.orientations[player] = MOVES[move]
        self.agents[player].orientation = self.orientations[player]
        # if self.positions[player] + move_delta == self.LEFT_WALL or self.positions[player] + move_delta == self.RIGHT_WALL:
        #     return REWARD_MOVE
        if radar[3 + move_delta] == WALL:
            return REWARD_WALL
        self.positions[player] += move_delta
        return REWARD_MOVE

    def is_within_range(self, attacker, attack):
        player_stance = self.stances[attacker]
        opponent_stance = self.stances[self.opponent(attacker)]
        if attack not in STANCE_HIT_MAP[player_stance][opponent_stance]:
            return False
        # if self.positions[attacker] == self.positions[self.opponent(attacker)]:
        #     return True
        radar = self.get_radar(attacker)
        target = radar[3 + self.orientations[attacker]]
        return target != WALL and target != '_'

    def reset_player_stance(self, player):
        if self.stances[player] == STANCE_STANDING:
            return
        previous_action = self.agents[player].previous_actions[1]
        if previous_action == ACTION_JUMP or previous_action == ACTION_CROUCH:
            self.stances[player] = STANCE_STANDING

    def do(self, player):
        reward = 0
        opponent = self.opponent(player)
        last_opponent_action = self.agents[opponent].previous_actions[0]
        action = self.agents[player].current_action

        self.reset_player_stance(player)
        if action in MOVES:
            reward += self.player_move(player, action)

        if action in STANCE_CHANGES:
            self.stances[player] = STANCE_CHANGES[action]
            reward += REWARD_MOVE

        if action in ATTACKS:
            if self.is_within_range(player, action):
                reward += REWARD_HIT
                self.inflict_damage_to(self.opponent(player))
                previous_actions = self.agents[player].previous_actions
                if previous_actions[0] in ATTACKS and previous_actions[1] in ATTACKS:
                    reward += REWARD_COMBO
            else:
                reward += REWARD_NONE

        if action == ACTION_DODGE:
            reward += REWARD_NONE

        if action == ACTION_NONE:
            reward += REWARD_NONE

        return reward, self.get_radar(player)

    def opponent_previous_actions(self, player):
        opponent = self.opponent(player)
        if self.agents[opponent] == {}:
            return [ACTION_NONE] * 3
        return self.agents[opponent].previous_actions

    def inflict_damage_to(self, opponent):
        self.agents[opponent].get_hit()


class LogicAgent:
    def __init__(self, environment, player_name, learning_rate, discount_factor, noise=0):
        self.noise = noise
        self.orientation = environment.orientations[player_name]
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.env = environment
        self.state = environment.radars[player_name]
        self.stance = STANCE_STANDING
        self.previous_state = self.state
        self.previous_actions = [ACTION_NONE, ACTION_NONE, ACTION_NONE]
        self.current_action = ACTION_NONE
        self.player_name = player_name
        self.health = 100
        self.qtable = {}
        self.score = 0

    def load_qtable(self, filename):
        if exists(filename):
            with open(filename, 'rb') as file:
                self.qtable = pickle.load(file)
            self.reset()

    def print_qtable(self):
        print('---' + self.player_name + ' QTABLE ---')
        for state, actions in self.qtable.items():
            positives_actions = dict([(a, p) for (a, p) in actions.items() if p > 0.0])
            if len(positives_actions) != 0:
                print(state, end=': ')
                max_action = max(positives_actions, key=positives_actions.get)
                print(f'{max_action}: {actions[max_action]}', end=', ')
                print('')
        print('----------------')

    def facing(self):
        return self.orientation == ORIENTATION_LEFT

    def reset(self):
        self.orientation = self.env.orientations[self.player_name]
        self.state = self.env.get_radar(self.player_name)
        self.health = 100
        self.score = 0

    def choose_action(self):
        if random() < self.noise:
            self.noise *= 0.999
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
        self.qtable[prev_state][self.current_action] += self.learning_rate * (
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

    def get_hit(self):
        self.health -= HIT_DAMAGE
        # self.score += REWARD_GET_HIT

    def is_dead(self):
        return self.health <= 0

    def get_health(self):
        return self.health

    def get_score(self):
        return self.score

    def win(self):
        self.score += REWARD_WIN
        self.update_qtable(REWARD_WIN, self.previous_state, self.state)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.qtable, file)


class Game:
    def __init__(self, learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR):
        self.player_list = None
        self.max_wins = MAX_WIN
        self.ryu_wins = 0
        self.ken_wins = 0
        self.wins = 0
        self.iterations = 0
        self.ken_score = []
        self.ryu_score = []
        self.Ryu = None
        self.Ken = None
        self.env = None
        self.wall_list = None
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exit_game = False

    def setup(self):
        self.env = LogicEnvironment(self.learning_rate, self.discount_factor)

        self.Ken = self.env.agents[KEN]
        self.Ken.set_position()
        self.Ken.load_qtable("KenQtable.qtable")

        self.Ryu = self.env.agents[RYU]
        self.Ryu.set_position()
        self.Ryu.load_qtable("RyuQtable.qtable")

    def check_end_game(self):
        if self.Ryu.is_dead() or self.Ken.is_dead():
            if self.Ryu.is_dead():
                self.Ken.win()
                self.ken_wins += 1
                self.ken_score.append(self.Ken.get_score())
                # self.display_victory(KEN)
            else:
                self.Ryu.win()
                self.ryu_wins += 1
                # self.display_victory(RYU)
                self.ryu_score.append(self.Ryu.get_score())
            self.env.reset()
            self.wins += 1
            # print(self.ken_wins + self.ryu_wins)

    def round(self):
        player_start = choice(PLAYERS)
        if player_start == RYU:
            self.Ryu.do()
        else:
            self.Ken.do()
        self.iterations += 1
        return player_start

    def end_game(self):
        # self.wins = self.max_wins
        self.env.reset()
        plt.figure(1)
        plt.plot(self.ryu_score, label="Ryu")
        plt.legend()
        plt.savefig(f"graphs/RYU_{self.wins}_l_{self.learning_rate}_d_{self.discount_factor}.png")

        plt.figure(2)
        plt.plot(self.ken_score, label="Ken")
        plt.legend()
        plt.savefig(f"graphs/KEN_{self.wins}_l_{self.learning_rate}_d_{self.discount_factor}.png")

        print(len(self.Ken.qtable))

        self.Ryu.save("RyuQtable.qtable")
        self.Ken.save("KenQtable.qtable")
        print(f"Ryu wins: {self.ryu_wins}, Ken wins: {self.ken_wins}")        
        
        self.exit_game = True
