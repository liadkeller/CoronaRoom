import logging

from common import shuffle_list

logger = logging.getLogger()

class Capsule:
    def __init__(self, index, rooms=None):
        self.index = index
        self.rooms = rooms if rooms else []
        self._update_constraints()
    
    def update(self, room_mapping):
        """
        Updates the capsule rooms according to the given room mapping
        """
        self.rooms = [room for room, capsule_index in room_mapping.items()
                           if self.index == capsule_index]
        self._update_constraints()
    
    def _update_constraints(self):
        """
        Updates the capsule constraints according to the capsule rooms
        """
        self.constraints = [c for room in self.rooms
                              for c in room.constraints]

    def apply_constraints(self, global_constraints):
        """
        Check if the capsule sustains the applied constraints
        The constraints are all of the capsule rooms constraints
        and any global constraints that are provided as argument.
        """
        self.constraints += global_constraints
        return self._is_valid()
    
    def _is_valid(self):
        """
        Check each of the capsule constraints
        Return an (is_valid, state) tuple where `is_valid` is a boolean
        and `state` is a list of actions that can be done to meet the constraint
        """
        ordered_constraints = sorted(self.constraints, key=lambda c: c.order)
        for constraint in ordered_constraints:
            valid, state = constraint.is_valid(self.index, self.rooms)
            if not valid:
                logger.debug((valid, [str(a) for a in state], constraint))
                return valid, state
        return True, []

class CapsulesManager:
    """
    This class represents the process of finding a single combination of valid capsules.
    """
    def __init__(self, rooms, capsules_count, global_constraints, config_json, existing_room_mapping=None):
        """
        Builds an instance of CapsulesManager object and tries to create a valid combination of capsules
        Tries a limited amount of tries according to config_json parameters
        Each try starts with a random room mapping and the manager tries to commit a limited amount of fixes to reach a valid combination
        """
        self.capsules_count = capsules_count
        self.global_constraints = global_constraints

        self.max_tries_count = config_json['max_tries_count']
        self.max_fixes_count = config_json['max_fixes_count']

        self.rooms = rooms
        self.room_mapping = {room: None for room in self.rooms.values()}

        for try_count in range(self.max_tries_count):
            logger.info(f'\nStart building capsules, attempt {try_count+1}/{self.max_tries_count}')
            succeded = self.build_capsules(existing_room_mapping)
            if succeded:
                return
        
        raise RuntimeError("Reached maximum try attempts")

    def allocate_rooms_randomly(self, room_indices):
        """
        Randomly allocates the given rooms to capsules
        
        Notice: This function changes self.room_mapping only
        self.capsules might not be defined at the time this functions is called
        """
        shuffled_rooms = shuffle_list(room_indices)
        shuffled_capsules = shuffle_list(range(self.capsules_count))

        factor = len(shuffled_rooms) // self.capsules_count

        # Allocates each section of the array to different capsule
        # Iterating the capsules in an ascending order while iterating the rooms in a random order
        for capsule_index in shuffled_capsules:
            for room_index in shuffled_rooms[capsule_index * factor: (capsule_index + 1) * factor]:
                room = self.rooms[room_index]
                self.room_mapping[room] = capsule_index
                logger.debug(f'Randomly allocating room {room.index} to capsule {capsule_index}')
        
        shuffled_capsules = shuffle_list(shuffled_capsules)
        # Allocates the remainder of the rooms array, one by one to another capsule
        # Notice: the list which is enumerated must be smaller then self.capsules_count or error will occur
        for capsule_index, room_index in zip(shuffled_capsules, shuffled_rooms[factor * self.capsules_count:]):
            room = self.rooms[room_index]
            self.room_mapping[room] = capsule_index
            logger.debug(f'Randomly allocating room {room.index} to capsule {capsule_index}')

    def randomize_room_mapping(self):
        """
        Randomize new room mapping.
        Allocate all rooms to new capsules.
        """
        self.allocate_rooms_randomly(self.rooms.keys())

    def build_capsules(self, existing_room_mapping=None):
        """
        Randomize capsules mapping and try to fix it
        Returns True if succeeded
        Returns False when reaches maximum fix attempts
        """
        if existing_room_mapping is None:
            self.randomize_room_mapping()
        else:
            self.room_mapping = existing_room_mapping

        self.capsules = {}

        for current_capsule_index in range(self.capsules_count):
            current_capsule = Capsule(current_capsule_index)
            current_capsule.update(self.room_mapping)
            self.capsules[current_capsule_index] = current_capsule
            
        for fix_count in range(self.max_fixes_count):
            logger.info(f'Attempting to fix capsules ({fix_count+1}/{self.max_fixes_count})')
            needed_fixing = self.fix_capsules()
            if not needed_fixing:
                return True
        
        if needed_fixing:
            return False
  
    def fix_capsules(self):
        """
        Apply global constaints and try to fix invalid capsules
        Return boolean if needed fixing
        """
        need_fixing = False
        for capsule in shuffle_list(self.capsules.values()):
            logger.debug(self.get_capsules())
            is_valid, actions = capsule.apply_constraints(self.global_constraints)
            if not is_valid:
                need_fixing = True
                for action in actions:
                    self.commit_action(action)
                break
        
        orphan_rooms = [room.index for room, capsule in self.room_mapping.items() if capsule is None]
        if len(orphan_rooms) > 0:
            self.allocate_rooms_randomly(orphan_rooms)
            self.update_capsules()
            need_fixing = True

        return need_fixing
    
    def commit_action(self, action):
        # The action only influence room_mapping so we must update the capsules
        action.do(self.room_mapping)
        self.update_capsules()
    
    def update_capsules(self):
        for capsule in self.capsules.values():
            capsule.update(self.room_mapping)
    
    def get_capsules(self):
        capsules = [[room.index for room in capsule.rooms] for capsule in self.capsules.values()]
        capsules.sort(key=lambda x:len(x) and x[0])
        return capsules
