# Introduction

**Hadoken** est un Street Fighter en apprentissage par renforcement par double Q-Learning, où deux IAs apprennent l'une face à l'autre.

La mécanique du jeu inclut un système de radar permettant de localiser son adversaire, la gestion d'une douzaine d'actions (déplacements gauche droite, sauter et se baisser, esquiver) et de coups avec une gestion de hauteur (low, middle et high punch, idem pour les kicks).

# Structure

## Modélisation
![IA RL Modélisation](https://github.com/user-attachments/assets/155fe88a-7537-4be5-87d2-ba45e96d5ba5)

## Actions possibles
![IA RL Actions](https://github.com/user-attachments/assets/bc1033cd-51ca-4670-bcbf-de82ebb5641a)

## qTable
![IA RL QTable](https://github.com/user-attachments/assets/59d847d4-5cd6-4a63-881a-b0a925b3adad)

# Lancement

Le jeu peut être lancé en mode graphique avec la librairie Arcade ou en ligne de commande pour accélérer la phase d'apprentissage.

## Mode graphique

```
python3 graphic.py
```

### Commandes en mode graphique

`R` : Ajout de noise

`M` : Réduction de la vitesse de visualisation (mode coup par coup)

`P` : Augmentation de la vitesse de la visualisation (mode d'apprentissage rapide) 

`Q` : Fin de jeu

## Mode ligne de commande

```
python3 no-graphic.py
```

# Crédits

Développeurs :

- Nathan Letourneau [@Nathan-dev-dot](https://github.com/Nathan-dev-dot)
- Théo Omnes [@ohmushi](https://github.com/ohmushi)
- Sarah Schlegel [@SarahSch19](https://github.com/SarahSch19)
