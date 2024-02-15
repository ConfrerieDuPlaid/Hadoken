import arcade
from logic import *


SPRITE_SIZE = 128
SPRITE_SCALE = 1
CHARACTER_SCALING = 2

WINDOW_VELOCITY_MAX = 999_999
WINDOW_VELOCITY_MIN = 20

SCREEN_WIDTH = SPRITE_SIZE * GRID_LIMIT
SCREEN_HEIGHT = 650
SCREEN_HEIGHT_SPACER = 40
SCREEN_TITLE = "Hadoken - Street Fighter!"
UPDATES_PER_FRAME = 5

ANIMATIONS = {
    ACTION_NONE: "none",
    ACTION_DODGE: "dodge",
    ACTION_JUMP: "jump",
    ACTION_CROUCH: "crouch",
    ACTION_PUNCH: "punch",
    ACTION_HIGH_PUNCH: "low_punch",
    ACTION_LOW_PUNCH: "high_punch",
    ACTION_HIGH_KICK: "high_kick",
    ACTION_LOW_KICK: "low_kick",
}

ANIMATIONS_LIST = list(ANIMATIONS.keys())


class Environment(LogicEnvironment):
    def __init__(self, learning_rate, discount_factor):
        super().__init__(learning_rate, discount_factor)
        self.agents = {
            KEN: Agent(self, KEN, learning_rate, discount_factor),
            RYU: Agent(self, RYU, learning_rate, discount_factor)
        }
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor


class Agent(arcade.Sprite, LogicAgent):
    def __init__(self, environment, player_name, learning_rate, discount_factor):
        arcade.Sprite.__init__(self)
        LogicAgent.__init__(self, environment, player_name, learning_rate, discount_factor)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING
        self.current_animation = 0
        self.animations = []
        self.load_textures(player_name)
        self.textures = self.animations
        self.noise = 1

    def load_textures(self, player_name):
        textures_path = f"./tiles/{player_name}/{player_name}"
        for k, v in ANIMATIONS.items():
            self.animations.append(arcade.load_texture(f"{textures_path}_{v}1.png"))
            self.animations.append(arcade.load_texture(f"{textures_path}_{v}-1.png"))

    def animation_index(self, action):
        if self.orientation == ORIENTATION_LEFT:
            return 2 * ANIMATIONS_LIST.index(action) + 1
        return 2 * ANIMATIONS_LIST.index(action)

    def set_position(self, center_x: float = 64, center_y: float = 192):
        self.center_x = self.env.positions[self.player_name] * SPRITE_SIZE + SPRITE_SIZE / 2
        self.center_y = SPRITE_SIZE + SPRITE_SIZE / 2
        if self.current_action not in ANIMATIONS_LIST:
            self.set_texture(self.animation_index(ACTION_NONE))
        else:
            self.set_texture(self.animation_index(self.current_action))


class Graphic(arcade.Window, Game):
    def __init__(self, learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR):
        arcade.Window.__init__(self, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        Game.__init__(self, learning_rate, discount_factor)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.gui_camera = None
        self.camera = None
        self.scene = None

    def create_scene(self):
        self.scene = arcade.Scene()
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)

        for x in range(0, SPRITE_SIZE * GRID_LIMIT, SPRITE_SIZE):
            wall = arcade.Sprite("./tiles/grassMid.png", SPRITE_SCALE)
            wall.center_x = x + SPRITE_SIZE / 2
            wall.center_y = SPRITE_SIZE / 2
            self.wall_list.append(wall)

    def setup(self):
        self.env = Environment(self.learning_rate, self.discount_factor)

        self.Ken = self.env.agents[KEN]
        self.Ken.set_position()
        # self.Ken.load_qtable("KenQtable.qtable")

        self.Ryu = self.env.agents[RYU]
        self.Ryu.set_position()
        # self.Ryu.load_qtable("RyuQtable.qtable")

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.Ryu)
        self.player_list.append(self.Ken)

        self.create_scene()

    def win_rate(self, wins):
        total_wins = self.ryu_wins + self.ken_wins
        if total_wins == 0:
            return 0
        return round(100 * wins / total_wins, 2)

    def draw_top_right_texts(self):
        to_print = [
            f'Ken win rate : {self.win_rate(self.ken_wins)} %',
            f'Ryu win rate : {self.win_rate(self.ryu_wins)} %',
            f'Iterations : {self.iterations}',
            f'Total wins : {self.ryu_wins + self.ken_wins}'
        ]
        for i in range(len(to_print)):
            arcade.draw_text(
                to_print[i], SCREEN_WIDTH - 300, SCREEN_HEIGHT - SCREEN_HEIGHT_SPACER * (i+1), arcade.color.BLACK, 20, bold=True)

    def print_ryu_vitals(self):
        to_print = [
            f'Ryu noise : {self.Ryu.noise}',
            f'Ryu Score: {self.Ryu.get_score()}',
            f'Ryu hp : {self.Ryu.health}',
        ]
        for i in range(len(to_print)):
            arcade.draw_text(
                to_print[i], SCREEN_WIDTH - 400, 10 + i * SCREEN_HEIGHT_SPACER, arcade.color.BLACK, 20, bold=True)

    def print_ken_vitals(self):
        to_print = [
            f'Ken noise : {self.Ken.noise}',
            f'Ken Score: {self.Ken.get_score()}',
            f'Ken hp : {self.Ken.health}',
        ]
        for i in range(len(to_print)):
            arcade.draw_text(
                to_print[i], 10, 10 + i * SCREEN_HEIGHT_SPACER, arcade.color.BLACK, 20, bold=True)

    def draw_texts(self):
        self.draw_top_right_texts()
        self.print_ryu_vitals()
        self.print_ken_vitals()
        arcade.draw_text(
            f'Ryu state : {self.Ryu.state} ', 10, SCREEN_HEIGHT - SCREEN_HEIGHT_SPACER, arcade.color.BLACK, 20, bold=True)
        arcade.draw_text(
            f'Ken state : {self.Ken.state} ', 10, SCREEN_HEIGHT - 2 * SCREEN_HEIGHT_SPACER, arcade.color.BLACK, 20, bold=True)


    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        self.player_list.draw()
        self.draw_texts()

    def on_update(self, delta_time: float):
        player_start = super().round()
        self.env.agents[player_start].set_position()
        self.player_list.update()

        self.check_end_game()
        if self.wins >= self.max_wins:
            self.end_game()
            exit(0)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q:
            self.end_game()
        if key == arcade.key.R:
            self.Ryu.noise = NOISE
            self.Ken.noise = NOISE
        if key == arcade.key.M:
            window.set_update_rate(1 / WINDOW_VELOCITY_MIN)
        if key == arcade.key.P:
            window.set_update_rate(1 / WINDOW_VELOCITY_MAX)


if __name__ == '__main__':
    window = Graphic()
    window.set_update_rate(1 / WINDOW_VELOCITY_MAX)
    window.setup()
    window.run()
