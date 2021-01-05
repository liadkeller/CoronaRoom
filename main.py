import json
import logging

from room import Room, Gender, build_rooms
from capsule import Capsule, CapsulesManager
from constraints import ConnectingConstraint, GenderConstraint, RoomCountConstraint

def read_json_file(filename):
    with open(filename) as file:
        return json.load(file)

def print_rooms(rooms):
    print('Rooms:')
    print('\n'.join(str(tup) for tup in rooms.values()))

def load_room_constraints(rooms, constraints_json):
    connecting_indices = constraints_json['connecting_constraints']
    gender_constraints_rooms_indices = constraints_json['gender_constraints']
    
    # relies on mapping from room number to max_room_count
    # Notice: JSON does not allow using integers as keys, so we parse the room_number string and convert it to integer
    harder_max_rooms_count_constraints = {int(room_number): max_room_count for room_number, max_room_count in constraints_json['harder_max_room_count_constraints'].items()}

    for i, j in connecting_indices:
        rooms[i].constraints.append(ConnectingConstraint(rooms[i], rooms[j]))
        rooms[j].constraints.append(ConnectingConstraint(rooms[i], rooms[j]))

    for i in gender_constraints_rooms_indices:
        rooms[i].constraints.append(GenderConstraint())
    
    for i, max_room_count in harder_max_rooms_count_constraints.items():
        rooms[i].constraints.append(RoomCountConstraint(max_room_count))

def main(data):
    roomates_dict = dict(enumerate(data['roomates'], start=1))
    roomates_gender = data['roomates_gender']
    constraints_json = data['constraints']
    existing_room_mapping = data.get('existing_room_mapping')

    rooms = build_rooms(roomates_dict, roomates_gender, assume_gender=True)
    load_room_constraints(rooms, constraints_json)

    global_max_room_count = constraints_json["global_max_room_count_constraint"]
    global_constraints = [
        RoomCountConstraint(global_max_room_count)
    ]

    config_json = data['config']
    generate_count = config_json['generate_count']
    capsules_count = config_json['capsules_count']

    solutions = set()

    for i in range(generate_count):
        try:
            manager = CapsulesManager(rooms, capsules_count, global_constraints, config_json, existing_room_mapping)

            solution = str(manager.get_capsules())

            if solution not in solutions:
                print(solution)
                solutions.add(solution)

        except RuntimeError:
            print('meh')

if __name__ == "__main__":
    logging.basicConfig()
    #logging.getLogger().setLevel(logging.INFO)

    data = read_json_file('data.json')
    main(data)