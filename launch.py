from subprocess import Popen

NOISES = (30, 40)  # 80
LEARNING_RATES = (40, 80)  # 90
DISCOUNT_FACTORS = (40, 80)  # 90


for noise in range(NOISES[0], NOISES[1] + 1, 5):
    for learning_rate in range(LEARNING_RATES[0], LEARNING_RATES[1] + 1, 5):
        for discount_factor in range(DISCOUNT_FACTORS[0], DISCOUNT_FACTORS[1] + 1, 5):
            # print(f"noise: {noise}, learning_rate: {learning_rate}, discount_factor: {discount_factor}")
            Popen(f"python3 main.py {noise} {learning_rate} {discount_factor}", shell=True)