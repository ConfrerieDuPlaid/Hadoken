import pickle

from matplotlib import pyplot as plt
from random import random, choice
import arcade

RYU = "Ryu"
KEN = "Ken"
PLAYERS = [RYU, KEN]

ACTION_LEFT, ACTION_RIGHT, ACTION_DODGE, ACTION_NONE = 'L', 'R', 'D', 'N'
ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH = 'P', 'K', 'LK', 'HK', 'LP', 'HP'
ACTIONS = [ACTION_LEFT, ACTION_RIGHT, ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH,
           ACTION_HIGH_PUNCH, ACTION_DODGE, ACTION_NONE]
ATTACKS = [ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH]

ORIENTATION_LEFT, ORIENTATION_RIGHT = -1, 1
ORIENTATIONS = [ORIENTATION_RIGHT, ORIENTATION_LEFT]
MOVES = {
    ACTION_LEFT: (-1, -1),
    ACTION_RIGHT: (1, 1),
}

REWARD_WIN = 1024
REWARD_LOSE = -2048
REWARD_WALL = -128
REWARD_HIT = 16
REWARD_GET_HIT = -32
REWARD_MOVE = -1
REWARD_NONE = -16
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

WALL = '#'
KEN_START = 2
RYU_START = 6

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

SPRITE_SCALE = 0.5
CHARACTER_SCALING = 0.7
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
    GRID_LIMIT = 10
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
        self.radars = {
            RYU: self.get_radar(RYU),
            KEN: self.get_radar(KEN),
        }

    def set_agents(self, ryu, ken):
        self.agents[RYU] = ryu
        self.agents[KEN] = ken

    def opponent(self, player):
        if player == KEN:
            return RYU
        return KEN

    def get_radar(self, player):
        radar = ['_'] * 7
        distance_opponent = self.distance_between_players()
        orientation_to_opponent = -sign(self.positions[player] - self.positions[self.opponent(player)])
        range_left_wall = distance_to_range(self.positions[player])
        range_right_wall = distance_to_range(self.RIGHT_WALL - self.positions[player])
        radar[3] = 'S'
        radar[3 - DISTANCES[range_left_wall]] = WALL
        radar[3 + DISTANCES[range_right_wall]] = WALL
        radar[3 + orientation_to_opponent * DISTANCES[distance_opponent]] = self.opponent(player)[0]
        return tuple(radar)

    def distance_between_players(self):
        return distance_to_range(abs(self.positions[RYU] - self.positions[KEN]))

    def player_move(self, player, move):
        radar = self.get_radar(player)
        move_delta, self.orientations[player] = MOVES[move]
        if radar[3 + move_delta] == WALL:
            return REWARD_WALL
        self.positions[player] += move_delta
        return REWARD_MOVE

    def is_within_range(self, attacker, attack):
        radar = self.get_radar(attacker)
        target = radar[3 + self.orientations[attacker]]
        return target != WALL and target != '_'  # todo not = self

    def do(self, player):
        reward = 0
        last_opponent_action = self.agents[self.opponent(player)].current_action
        damage_inflicted = False
        action = self.agents[player].current_action
        if action in MOVES:
            reward += self.player_move(player, action)
            reward += REWARD_MOVE

        if action in ATTACKS:
            if self.is_within_range(player, action):
                if last_opponent_action == ACTION_DODGE:
                    reward -= REWARD_HIT
                else:
                    reward += REWARD_HIT
                    damage_inflicted = True
            else:
                reward -= REWARD_HIT
                damage_inflicted = True

        if action == ACTION_DODGE:
            if last_opponent_action in ATTACKS:
                reward += REWARD_HIT
            else:
                reward -= REWARD_HIT

        if action == ACTION_NONE:
            reward -= REWARD_NONE

        return reward, damage_inflicted, (self.get_radar(player), self.orientations[player])

    def inflict_damage(self, player):
        opponent = self.opponent(player)
        self.agents[opponent].get_hit()

    def print_map(self):
        for i in range(self.GRID_LIMIT):
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


class Agent(arcade.Sprite):
    def __init__(self, environment, player_name, learning_rate=0.45, discount_factor=0.55):
        super().__init__()
        image_source = "./tiles/femaleAdventurer.png"
        self.player_sprite = arcade.Sprite(image_source, CHARACTER_SCALING)
        self.player_sprite.center_x = 64
        self.player_sprite.center_y = 128

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.env = environment
        self.state = environment.radars[player_name]
        self.previous_state = self.state
        self.previous_action = ACTION_NONE
        self.current_action = ACTION_NONE
        self.player_name = player_name
        self.health = 100
        self.qtable = {}
        self.score = 0

    def reset(self):
        self.state = self.env.radars[self.player_name]
        self.health = 100
        self.score = 0

    def choose_action(self):
        if random() < 0.5:
            self.current_action = choice(ACTIONS)
            return
        self.add_qtable_state(self.state)
        self.current_action = arg_max(self.qtable[self.state])

    def add_qtable_state(self, state):
        if state not in self.qtable.keys():
            self.qtable[state] = {}
            for a in ACTIONS:
                self.qtable[state][a] = 0.0

    def update_qtable(self, reward, prev_state, new_state, action_taken=""):
        if action_taken == "":
            action_taken = self.current_action
        self.add_qtable_state(prev_state)
        self.add_qtable_state(new_state)
        max_q = max(self.qtable[new_state].values())
        self.qtable[prev_state][self.previous_action] += self.learning_rate * (
                reward + self.discount_factor * max_q - self.qtable[prev_state][self.current_action])
        # print(f"{self.player_name}: {self.current_action} {self.get_state()}")

    def do(self):
        self.choose_action()
        reward, damage_inflicted, new_state = self.env.do(self.player_name)
        self.score += reward

        self.update_qtable(reward, self.state, new_state)
        self.previous_state = self.state
        self.previous_action = self.current_action
        self.state = new_state
        if damage_inflicted:
            self.env.inflict_damage(self.player_name)
        return self.current_action

    def get_state(self):
        return f"{self.previous_state} {self.qtable[self.previous_state]}"

    def get_hit(self):
        self.health -= HIT_DAMAGE
        # self.update_qtable(REWARD_GET_HIT, self.previous_state, self.state, self.previous_action)

    def is_dead(self):
        return self.health <= 0

    def get_health(self):
        return self.health

    def get_score(self):
        return self.score

    def win(self):
        self.score += REWARD_WIN
        self.update_qtable(REWARD_WIN, self.previous_state, self.state, action_taken=self.previous_action)

    def lose(self):
        self.score += REWARD_LOSE
        self.update_qtable(REWARD_LOSE, self.previous_state, self.state, action_taken=self.previous_action)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.qtable, file)


class Graphic(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.player_list = None
        self.ryu_wins = None
        self.max_wins = None
        self.ken_wins = None
        self.wins = None
        self.iterations = None
        self.ken_score = None
        self.ryu_score = None
        self.Ryu = None
        self.Ken = None
        self.env = None
        self.gui_camera = None
        self.camera = None
        self.scene = None
        self.wall_list = None


    def setup(self):
        self.env = Environment()
        self.Ryu = Agent(self.env, RYU)
        self.Ken = Agent(self.env, KEN)
        self.env.set_agents(self.Ryu, self.Ken)
        self.ryu_score = []
        self.ken_score = []
        self.player_list = arcade.SpriteList()

        self.player_list.append(self.Ryu.player_sprite)
        self.player_list.append(self.Ken.player_sprite)

        self.iterations = 0
        self.wins = 0
        self.max_wins = 100
        self.ken_wins, self.ryu_wins = 0, 0

        self.scene = arcade.Scene()
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)

        for x in range(0, 1250, 64):
            wall = arcade.Sprite("./tiles/grassMid.png", SPRITE_SCALE)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        self.player_list.draw()

    def on_update(self, delta_time: float):
        player_start = choice(PLAYERS)
        if player_start == RYU:
            self.Ryu.do()
            self.Ken.do()
        else:
            self.Ken.do()
            self.Ryu.do()
        self.iterations += 1

        print(
            f"N°{self.iterations} - "
            f"Ryu: {{{self.Ryu.current_action} {self.env.orientations[RYU]}/{self.Ryu.get_health()} {self.Ryu.get_score()}}} "
            f"Ken: {{{self.Ken.current_action} {self.env.orientations[KEN]}/{self.Ken.get_health()} {self.Ken.get_score()}}} ",
            end="")
        self.env.print_map()

        if self.Ryu.is_dead() or self.Ken.is_dead():
            if self.Ryu.is_dead():
                self.Ryu.lose()
                self.Ken.win()
                self.ken_wins += 1
                print("KEN WINS!")
            else:
                self.Ryu.win()
                self.Ken.lose()
                self.ryu_wins += 1
                print("RYU WINS!")
            self.env.reset()
            self.ken_score.append(self.Ken.get_score())
            self.ryu_score.append(self.Ryu.get_score())
            self.Ryu.reset()
            self.Ken.reset()
            self.wins += 1

        if self.wins == self.max_wins:
            plt.plot(self.ryu_score, label="Ryu")
            plt.plot(self.ken_score, label="Ken")
            self.Ryu.save("RyuQtable.qtable")
            self.Ken.save("KenQtable.qtable")
            print(f"Ryu wins: {self.ryu_wins}, Ken wins: {self.ken_wins}")
            plt.legend()
            plt.show()
            exit(0)


if __name__ == '__main__':
    window = Graphic()
    window.setup()
    window.run()
