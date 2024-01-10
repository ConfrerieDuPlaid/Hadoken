from random import random, choice

from matplotlib import pyplot as plt

RYU = "Ryu"
KEN = "Ken"

ORIENTATION_RIGHT, ORIENTATION_LEFT = -1, 1
ORIENTATIONS = [ORIENTATION_RIGHT, ORIENTATION_LEFT]

ACTION_LEFT, ACTION_RIGHT, ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH = 'L', 'R', 'P', 'K', 'LK', 'HK', 'LP', 'HP'

ACTIONS = [ACTION_LEFT, ACTION_RIGHT, ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH,
           ACTION_HIGH_PUNCH]
MOVES = {
    ACTION_LEFT: (-1, -1),
    ACTION_RIGHT: (1, 1),
}
ATTACKS = [ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH]

REWARD_WIN = 1000
REWARD_LOSE = -1000
REWARD_HIT = 10
REWARD_GET_HIT = -40
REWARD_MOVE = -5

REWARD_COOLDOWN = -10
REWARD_DODGE = 15
REWARD_DODGE_MISS = -15
REWARD_WALL = -100
# todo modifier les rewards

NEAR, MID, FAR = 'N', 'M', 'F'
DISTANCES = {
    NEAR: 1,
    MID: 2,
    FAR: 3,
}

STANDING, CROUCHING, JUMPING = 'S', 'C', 'J'
STANCES = [STANDING, CROUCHING, JUMPING]


def arg_max(table):
    return max(table, key=table.get)


class Environment:
    GRID_LIMIT = 5

    def __init__(self, ken_start=2, ryu_start=-2):
        self.positions = {
            KEN: ken_start,
            RYU: ryu_start,
        }
        self.state = {
            RYU: (self.distance_between_players(), ORIENTATION_RIGHT),  # self.distance_between_players()
            KEN: (self.distance_between_players(), ORIENTATION_LEFT),
        }

    def reset(self):
        self.positions = {
            KEN: 2,
            RYU: -2,
        }
        self.state = {
            RYU: (self.distance_between_players(), ORIENTATION_RIGHT),  # self.distance_between_players()
            KEN: (self.distance_between_players(), ORIENTATION_LEFT),
        }

    def do(self, player, action):  # retourne tuple (reward, ∂HP, state)
        reward = 0
        damage = 0
        if action in MOVES:
            reward += self.update_player_position(player, action)
            reward += REWARD_MOVE

        if action in ATTACKS:
            if self.is_within_range(player, action):
                reward += REWARD_HIT
                damage = 10
                # todo range/dodge/etc.
            else:
                reward -= REWARD_HIT

        return reward, damage, self.state[player]

    # def swap_defender(self, attacker, ryu_action, ken_action):
    #     defender = RYU if attacker == KEN else KEN
    #     attacker_action = ryu_action if attacker == RYU else ken_action
    #     defender_action = ryu_action if attacker == KEN else ken_action
    #     return defender, attacker_action, defender_action

    def is_within_range(self, attacker, attack):
        defender = RYU if attacker == KEN else KEN
        return (DISTANCES[self.distance_between_players()] == 1 and
                self.state[attacker][1] + self.positions[attacker]
                == self.positions[defender])

    @staticmethod
    def map_distance_to_range(distance):
        if distance == 1:
            return NEAR
        elif distance == 2:
            return MID
        else:
            return FAR

    def distance_between_players(self):
        return self.map_distance_to_range(abs(self.positions[RYU] - self.positions[KEN]))

    def update_player_position(self, player, action):  # retourne une reward
        move, new_orientation = MOVES[action]
        new_position = self.positions[player] + move
        reward = 0
        if -self.GRID_LIMIT <= new_position <= self.GRID_LIMIT:
            self.positions[player] = new_position
            self.state[RYU] = (
                self.distance_between_players(), new_orientation if player == RYU else self.state[RYU][1])
            self.state[KEN] = (
                self.distance_between_players(), new_orientation if player == KEN else self.state[KEN][1])
        else:
            reward += REWARD_WALL
        return reward

    def get_player_positions(self):
        return self.positions[RYU], self.positions[KEN]

    def print_map(self):
        for i in range(-self.GRID_LIMIT, self.GRID_LIMIT + 1):
            if self.positions[RYU] == i and self.positions[KEN] == i:
                print('O', end='')
            elif self.positions[RYU] == i:
                print(RYU[0], end='')
            elif self.positions[KEN] == i:
                print(KEN[0], end='')
            else:
                print('_', end='')
        print()


class Agent:
    def __init__(self, env, player_name):
        self.env = env
        self.state = self.env.state[player_name]
        self.player_name = player_name
        self.health = 100
        self.qtable = {}
        self.score = 0
        for distance in DISTANCES:
            for orientation in ORIENTATIONS:
                self.qtable[(distance, orientation)] = {}
                for action in ACTIONS:
                    self.qtable[(distance, orientation)][action] = 0.0

    def reset(self):
        self.state = self.env.state[self.player_name]
        self.health = 100
        self.score = 0

    def choose_action(self):
        if random() < 0.01:
            return choice(ACTIONS)
        return arg_max(self.qtable[self.state])

    def do(self, learning_rate=0.7, discount_factor=0.3):
        action = self.choose_action()
        reward, damage, new_state = self.env.do(self.player_name, action)
        self.score += reward

        maxQ = max(self.qtable[new_state].values())
        self.qtable[self.state][action] += learning_rate * (
                reward + discount_factor * maxQ - self.qtable[self.state][action])

        self.state = new_state
        return action, damage

    def is_dead(self):
        return self.health <= 0

    def get_health(self):
        return self.health

    def get_score(self):
        return self.score

    def get_hit(self, hit_damage):
        self.health -= hit_damage


if __name__ == '__main__':
    street_fighter_env = Environment()
    Ryu = Agent(street_fighter_env, RYU)
    Ken = Agent(street_fighter_env, KEN)
    ryu_score = []
    ken_score = []

    iterations = 0
    wins = 0
    while wins < 100:
        if Ryu.is_dead() or Ken.is_dead():
            street_fighter_env.reset()
            ken_score.append(Ken.get_score())
            ryu_score.append(Ryu.get_score())
            Ryu.reset()
            Ken.reset()
            wins += 1

        iterations += 1
        action_Ryu, damage = Ryu.do()
        Ken.get_hit(damage)
        action_Ken, damage = Ken.do()
        Ryu.get_hit(damage)

        print(
            f"Iteration {iterations} - Ryu: {action_Ryu} {street_fighter_env.state[RYU][1]}, Ken: {action_Ken} {street_fighter_env.state[KEN][1]}")
        print(f"Ryu {street_fighter_env.get_player_positions()} Ken")
        street_fighter_env.print_map()
        print("Ryu Health:", Ryu.get_health())
        print("Ken Health:", Ken.get_health())
        print("Ryu Score:", Ryu.get_score())
        print("Ken Score:", Ken.get_score())

    plt.plot(ryu_score, label="Ryu")
    plt.plot(ken_score, label="Ken")
    plt.legend()
    plt.show()


