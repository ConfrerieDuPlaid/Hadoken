from random import choice

RYU = "Ryu"
KEN = "Ken"

ORIENTATION_RIGHT, ORIENTATION_LEFT = -1, 1

ACTION_LEFT, ACTION_RIGHT, ACTION_DODGE, ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH, ACTION_COOLDOWN = 'L', 'R', 'D', 'P', 'K', 'LK', 'HK', 'LP', 'HP', 'CD'

ACTIONS = [ACTION_LEFT, ACTION_RIGHT, ACTION_DODGE, ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH, ACTION_COOLDOWN]
MOVES = {
    ACTION_LEFT: (-1, -1),
    ACTION_RIGHT: (1, 1),
}
ATTACKS = [ACTION_PUNCH, ACTION_KICK, ACTION_LOW_KICK, ACTION_HIGH_KICK, ACTION_LOW_PUNCH, ACTION_HIGH_PUNCH]

REWARD_MOVE = -1
REWARD_ATTACKS = {
    ACTION_PUNCH: 10,
    ACTION_LOW_PUNCH: 10,
    ACTION_HIGH_PUNCH: 10,
    ACTION_KICK: 20,
    ACTION_LOW_KICK: 20,
    ACTION_HIGH_KICK: 20,
}
REWARD_ATTACKS_MISS = {
    ACTION_PUNCH: -10,
    ACTION_LOW_PUNCH: -10,
    ACTION_HIGH_PUNCH: -10,
    ACTION_KICK: -20,
    ACTION_LOW_KICK: -20,
    ACTION_HIGH_KICK: -20,
}
REWARD_COOLDOWN = -10
REWARD_DODGE = 15
REWARD_DODGE_MISS = -15
REWARD_WALL = -100

NEAR, MID, FAR = 'N', 'M', 'F'
DISTANCES = {
    NEAR: 1,
    MID: 2,
    FAR: 3,
}
ATTACK_RANGES = {
    ACTION_PUNCH: NEAR,
    ACTION_LOW_PUNCH: NEAR,
    ACTION_HIGH_PUNCH: NEAR,
    ACTION_KICK: MID,
    ACTION_LOW_KICK: MID,
    ACTION_HIGH_KICK: MID,
}


class Environment:
    GRID_LIMIT = 5

    def __init__(self):
        self.players = {
            RYU: {'position': -2, 'health': 100, 'score': 0, 'orientation': ORIENTATION_LEFT},
            KEN: {'position': 2, 'health': 100, 'score': 0, 'orientation': ORIENTATION_RIGHT}
            #TODO refactor orientation
        }
        self.state = (self.players[RYU]['position'], self.players[KEN]['position'])

    def do(self, ryu_action, ken_action):
        if ryu_action in MOVES:
            self.update_player_position(RYU, ryu_action)

        if ken_action in MOVES:
            self.update_player_position(KEN, ken_action)

        for attacker in self.players.keys():
            defender, attacker_action, defender_action = self.swap_defender(attacker, ryu_action, ken_action)

            if attacker_action in ATTACKS:
                if self.is_within_range(attacker, attacker_action):
                    if defender_action == ACTION_DODGE:
                        self.players[attacker]['score'] += REWARD_ATTACKS_MISS[attacker_action]
                    else:
                        self.players[attacker]['score'] += REWARD_ATTACKS[attacker_action]
                else:
                    self.players[attacker]['score'] += REWARD_ATTACKS_MISS[attacker_action]
            elif attacker_action == ACTION_DODGE:
                if defender_action in ATTACKS and self.is_within_range(defender, defender_action):
                    self.players[attacker]['score'] += REWARD_DODGE
                else:
                    self.players[attacker]['score'] += REWARD_DODGE_MISS

            if defender_action in ATTACKS:
                if self.is_within_range(defender, defender_action):
                    if attacker_action != ACTION_DODGE:
                        self.players[attacker]['health'] -= REWARD_ATTACKS[defender_action]
                        if self.players[attacker]['health'] < 0:
                            self.players[attacker]['health'] = 0

    def swap_defender (self, attacker, ryu_action, ken_action):
        defender = RYU if attacker == KEN else KEN
        attacker_action = ryu_action if attacker == RYU else ken_action
        defender_action = ryu_action if attacker == KEN else ken_action
        return defender, attacker_action, defender_action

    def is_within_range(self, attacker, attack):
        defender = RYU if attacker == KEN else KEN
        attack_range = ATTACK_RANGES[attack]
        return (self.distance_between_players() == 1 and
                DISTANCES[attack_range] * self.players[attacker]['orientation'] + self.players[attacker]['position']
                == self.players[defender]['position'])

    def distance_between_players(self):
        return abs(self.players[RYU]['position'] - self.players[KEN]['position'])

    def update_player_position(self, player, action):
        new_position, self.players[player]['orientation'] = MOVES[action]
        new_position += self.players[player]['position']
        if -self.GRID_LIMIT <= new_position <= self.GRID_LIMIT:
            self.players[player]['position'] = new_position
            self.players[player]['score'] += REWARD_MOVE
        else:
            self.players[player]['score'] += REWARD_WALL

    def get_player_positions(self):
        return self.players[RYU]['position'], self.players[KEN]['position']

    def get_player_health(self, player_name):
        return self.players[player_name]['health']

    def get_player_score(self, player_name):
        return self.players[player_name]['score']

    def is_game_over(self):
        return any(player['health'] <= 0 for player in self.players.values())

    def print_map(self):
        for i in range(-self.GRID_LIMIT, self.GRID_LIMIT+1):
            if self.players[RYU]['position'] == i and self.players[KEN]['position'] == i:
                print('O', end='')
            elif self.players[RYU]['position'] == i:
                print(RYU[0], end='')
            elif self.players[KEN]['position'] == i:
                print(KEN[0], end='')
            else:
                print('_', end='')
        print()


class Agent:
    def __init__(self, env, player_name):
        self.env = env
        self.player_name = player_name
        self.health = 100
        self.qtable = {}
        # for state in env.map:
        #     self.qtable[state] = {}
        #     for action in ACTIONS:
        #         self.qtable[state][action] = 0.0

    def choose_action(self):
        return choice(ACTIONS)

    def do(self):
        action = self.choose_action()
        return action


if __name__ == '__main__':
    street_fighter_env = Environment()
    Ryu = Agent(street_fighter_env, RYU)
    Ken = Agent(street_fighter_env, KEN)

    iterations = 0
    while not street_fighter_env.is_game_over():
        iterations += 1
        action_Ryu = Ryu.do()
        action_Ken = Ken.do()
        street_fighter_env.do(action_Ryu, action_Ken)

        print(f"Iteration {iterations} - Ryu: {action_Ryu}, Ken: {action_Ken}")
        print(f"Ryu {street_fighter_env.get_player_positions()} Ken")
        street_fighter_env.print_map()
        print("Ryu Health:", street_fighter_env.get_player_health(RYU))
        print("Ken Health:", street_fighter_env.get_player_health(KEN))
        print("Ryu Score:", street_fighter_env.get_player_score(RYU))
        print("Ken Score:", street_fighter_env.get_player_score(KEN))

    print("Game Over!")
