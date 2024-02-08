import arcade

# Dimensions de la fenêtre
LARGEUR_FENETRE = 800
HAUTEUR_FENETRE = 600
TITRE_FENETRE = "Animation de Sprite"

# Dimensions du sprite
LARGEUR_SPRITE = 128
HAUTEUR_SPRITE = 128


class player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.animations = [
            arcade.load_texture("./tiles/Ken/Ken_idle.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk1.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk2.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk3.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk4.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk5.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk6.png"),
            arcade.load_texture("./tiles/Ken/Ken_walk7.png"),
            # Ajoutez toutes les images de votre animation
        ]


class MonJeu(arcade.Window):
    def __init__(self, largeur, hauteur, titre):
        super().__init__(largeur, hauteur, titre)
        self.anim = 0
        self.sprite = player()
        self.current_frame = 0
        self.animation_speed = 0.1  # Vitesse de l'animation

    def setup(self):
        # Chargez les images de votre animation dans une liste

        # Créez un sprite et attribuez-lui les images
        self.sprite.center_x = LARGEUR_FENETRE // 2
        self.sprite.center_y = HAUTEUR_FENETRE // 2
        self.sprite.textures = self.sprite.animations

    def on_draw(self):
        arcade.start_render()
        self.sprite.draw()

    def update(self, delta_time):
        if self.anim > 6:
            self.anim = 0
        else:
            self.anim += 1
        self.sprite.set_texture(self.anim)


def main():
    jeu = MonJeu(LARGEUR_FENETRE, HAUTEUR_FENETRE, TITRE_FENETRE)
    jeu.setup()
    jeu.set_update_rate(1 / 15)
    arcade.run()


if __name__ == "__main__":
    main()
