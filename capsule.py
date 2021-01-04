import random

class Capsule:
    def __init__(self, index, rooms):
        self.index = index
        self.rooms = rooms
        self.constraints = [c for room in rooms
                              for c in room.constraints]
    
    def add(self, room):
        self.rooms.append(room)
        self.constraints += room.constraints
    
    def remove(self, room):
        self.rooms.remove(room)
        self.constraints = [c for room in self.rooms
                              for c in room.constraints]

    def apply_constraints(self, global_constraints):
        self.constraints += global_constraints

        for constraint in self.constraints:
            self._valid, self._state = self._is_valid()
            if not self._valid:
                return self._valid, self._state

        return self._valid, self._state
    
    def _is_valid(self):
        ordered_constraints = sorted(self.constraints, key=lambda c: c.order)
        for constraint in ordered_constraints:
            valid, state = constraint.is_valid(self.index, self.rooms)
            if not valid:
                return valid, state
        return True, []

class CapsulesManager:
    max_tries_count = 20
    max_fixes_count = 20

    def __init__(self, rooms, capsules_count, global_constraints):
        self.global_constraints = global_constraints

        self.rooms = rooms
        self.room_mapping = {room: None for room in self.rooms}

        self.capsules_count = capsules_count

        for try_count in range(CapsulesManager.max_tries_count):
            succeded = self.build_capsules()
            if succeded:
                self.print_capsules()
                return
        
        raise RuntimeError("Reached maximum try attempts")

    def randomize_room_mapping(self):
        shuffled_rooms = list(self.rooms)
        random.shuffle(shuffled_rooms)
        factor = len(shuffled_rooms) // self.capsules_count
        for capsule_index in range(self.capsules_count):
            for room_index in shuffled_rooms[capsule_index * factor: (capsule_index + 1) * factor]:
                room = self.rooms[room_index]
                self.room_mapping[room] = capsule_index
                print(f'Randomly allocating room {room.index} to capsule {capsule_index}')
        for room_index in shuffled_rooms[factor * self.capsules_count:]:
            room = self.rooms[room_index]
            for capsule_index in range(self.capsules_count):
                self.room_mapping[room] = capsule_index
                print(f'Randomly allocating room {room.index} to capsule {capsule_index}')

    def build_capsules(self):
        """
        Randomize capsules mapping and try to fix it
        Returns True if succeeded
        Returns False when reaches maximum fix attempts
        """
        self.randomize_room_mapping()
        self.capsules = {}

        for current_capsule_index in range(self.capsules_count):
            capsule_rooms = []
            for room, capsule_index in self.room_mapping.items():
                if current_capsule_index == capsule_index:
                    capsule_rooms.append(room)
            self.capsules[current_capsule_index] = Capsule(current_capsule_index, capsule_rooms)
        
        for fix_count in range(CapsulesManager.max_fixes_count):
            needed_fixing = self.fix_capsules()
            if not needed_fixing:
                return True
        
        if needed_fixing:
            return False
  
    def fix_capsules(self):
        '''
        Apply global constaints and try to fix invalid capsules
        Return voolean if needef fixing
        '''
        need_fixing = False
        for capsule in self.capsules.values():
            is_valid, actions = capsule.apply_constraints(self.global_constraints)
            if not is_valid:
                need_fixing = True
                for action in actions:
                    self.commit_action(action)
        return need_fixing
    
    def commit_action(self, action):
        action.do(self.capsules, self.room_mapping)
    
    def print_capsules(self):
        print(self.room_mapping)
