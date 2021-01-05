from enum import Enum

class Room:
    def __init__(self, index, roomates, gender):
        self.index = index
        self.roomates = roomates
        self.gender = gender
        self.count = len(roomates)
        self.constraints = []

    def __repr__(self):
        return repr((self.index, self.roomates, self.gender, self.count,
                    [c for c in self.constraints]))

class Gender(Enum):
    Female = 0
    Male = 1


def build_rooms(roomates_dict: dict, gender_dict: dict, assume_gender):
    """
    :roomates_dict maps room_index to roomates_names, i.e.
    {
        1: ['Johnny', 'Papi'],
        2: ['Danny']
    }

    Roomates names MUST BE UNIQUE otherwise bugs WILL OCCUR.

    :gender_dict maps names to genders. i.e
    {
        'Johnny': Gender.Male,   (You can write 0, 1 instead and i will take care of it)
        'Rina': Gender.Female
    }

    Names here are from the pool of all roomates names provided.

    if assume_gender is True, assumes gender is defaultly Male
    """
    rooms_dict = {}
    for i, roomates in roomates_dict.items():
        for roomate in roomates:
            # if roomate gender appears in gender_dict, set it as the room gender
            # Notice: Wrong gender of the first roomate will turn the entire room to the wrong gender
            room_gender = gender_dict.get(roomate, None)
            if room_gender:
                break
        
        if room_gender is None:
            if assume_gender:
                room_gender = Gender.Male
            else:
                raise ValueError(f"Could not find gender for room {i}")

        rooms_dict[i] = Room(i, roomates, room_gender)
    return rooms_dict
