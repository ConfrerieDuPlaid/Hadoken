import pickle
from os.path import exists

from matplotlib import pyplot as plt
from random import random, choice
import arcade
from logic import *


SPRITE_SIZE = 128
SPRITE_SCALE = 1
CHARACTER_SCALING = 2

SCREEN_WIDTH = SPRITE_SIZE * GRID_LIMIT
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Hadoken - Street Fighter!"
UPDATES_PER_FRAME = 5

ANIMATIONS = {
    ACTION_NONE: "none",
    ACTION_DODGE: "dodge",
    ACTION_JUMP: "jump",
    ACTION_CROUCH: "crouch",
    ACTION_HIGH_KICK: "high_kick",
    ACTION_LOW_KICK: "low_kick",
    ACTION_PUNCH: "punch",
}

ANIMATIONS_LIST = list(ANIMATIONS.keys())


class Environment(LogicEnvironment):
    def __init__(self, learning_rate=0.60, discount_factor=0.80):
        super().__init__(learning_rate, discount_factor)
        self.agents = {
            KEN: Agent(self, KEN, 1, learning_rate, discount_factor),
            RYU: Agent(self, RYU, -1, learning_rate, discount_factor)
        }


class Agent(arcade.Sprite, LogicAgent):
    def __init__(self, environment, player_name, default_orientation=1, learning_rate=0.60, discount_factor=0.80):
        arcade.Sprite.__init__(self)
        LogicAgent.__init__(self, environment, player_name, default_orientation, learning_rate, discount_factor)
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
        self.center_y = SPRITE_SIZE + SPRITE_SIZE
        if self.current_action not in ANIMATIONS_LIST:
            self.set_texture(ANIMATIONS_LIST.index(ACTION_NONE))
        else:
            self.set_texture(ANIMATIONS_LIST.index(self.current_action))


class Graphic(arcade.Window, Game):
    def __init__(self, learning_rate=0.5, discount_factor=0.5):
        arcade.Window.__init__(self, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        Game.__init__(self, learning_rate, discount_factor)
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
        self.env = Environment()

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

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        self.player_list.draw()
        arcade.draw_text(
            f'Iterations : {self.iterations} Ryu Score: {self.Ryu.get_score()} Ken Score: {self.Ken.get_score()} Total wins : {self.ryu_wins + self.ken_wins}',
            10, 10, arcade.color.RED, 24, bold=True)

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
            self.Ryu.noise = 1
            self.Ken.noise = 1


if __name__ == '__main__':
    window = Graphic()
    window.set_update_rate(1 / 999999)
    window.setup()
    window.run()
