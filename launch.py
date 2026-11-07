import sys
from subprocess import Popen

LEARNING_RATES = (40, 80)  # 90
DISCOUNT_FACTORS = (20, 80)  # 90

for learning_rate in range(LEARNING_RATES[0], LEARNING_RATES[1] + 1, 5):
    for discount_factor in range(DISCOUNT_FACTORS[0], DISCOUNT_FACTORS[1] + 1, 5):
        # sys.executable : même interpréteur (et donc même venv) que launch.py
        Popen([sys.executable, "no-graphic.py", str(learning_rate), str(discount_factor)])

