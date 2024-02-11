import os

NOISES = (30, 50)  # 80
LEARNING_RATES = (20, 40)  # 90
DISCOUNT_FACTORS = (20, 40)  # 90


for noise in range(NOISES[0], NOISES[1] + 10, 10):
    for learning_rate in range(LEARNING_RATES[0], LEARNING_RATES[1] + 10, 10):
        for discount_factor in range(DISCOUNT_FACTORS[0], DISCOUNT_FACTORS[1] + 10, 10):
            print(f"noise: {noise}, learning_rate: {learning_rate}, discount_factor: {discount_factor}")
            os.system(f"python main.py {learning_rate} {discount_factor} {noise}")