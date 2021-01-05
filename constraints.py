from collections import Counter

from common import shuffle_list

class Constraint:
    def is_valid(self, capsule_index, rooms):
        """
        Return (is_valid, state)
        `is_valid` is a boolean
        `state` is an arbitrary suggestion of how to fix so the room will be valid
        """
        raise NotImplementedError()
    
    def __repr__(self):
        return f"{self.__class__.__name__}"

class GenderConstraint(Constraint):
    order = 20

    def is_valid(self, capsule_index, rooms):
        gender_counter = Counter(room.gender for room in rooms)
        if len(gender_counter) == 1:
            # only one gender
            return True, []
        
        elif len(gender_counter) == 2:
            least_common_gender, _ = gender_counter.most_common()[-1]
            return False, [Reduce(capsule_index, room) for room in rooms if room.gender == least_common_gender]
        
        raise ValueError(f'Cannot have {len(gender_counter)} genders.')

class RoomCountConstraint(Constraint):
    def __init__(self, max_room_count):
        self.max_room_count = max_room_count
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_room_count})"
    
    @property
    def order(self):
        return (self.max_room_count - 2) * 8

    def is_valid(self, capsule_index, rooms):
        valid = (len(rooms) <= self.max_room_count)
        state = []
        if not valid:
            to_reduce = len(rooms) - self.max_room_count
            state = [Reduce(capsule_index, room) for room in shuffle_list(rooms)[:to_reduce]]
        return valid, state

class ConnectingConstraint(Constraint):
    order = 10
    def __init__(self, room1, room2):
        self.room1 = room1
        self.room2 = room2

    def __repr__(self):
        return f"{self.__class__.__name__}({self.room1.index}, {self.room2.index})"

    def is_valid(self, capsule_index, rooms):
        if (self.room1 in rooms) ^ (self.room2 in rooms):
            for room in (self.room1, self.room2):
                if room not in rooms:
                    return False, [Add(capsule_index, room)]
        return True, []


class Action:
    def __init__(self, capsule_index, room):
        self.capsule_index = capsule_index
        self.room = room
    
    def __repr__(self):
        return f'{self.__class__.__name__}(Capsule={self.capsule_index}, Room={self.room.index})'

class Reduce(Action):
    def do(self, room_mapping):
        room_mapping[self.room] = None

class Add(Action):
    def do(self,room_mapping):
        room_mapping[self.room] = self.capsule_index