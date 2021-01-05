import random

def shuffle_list(iterable):
    shuffled_list = list(iterable)
    random.shuffle(shuffled_list)
    return shuffled_list
