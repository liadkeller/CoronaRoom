import logging

from common import shuffle_list

logger = logging.getLogger()

class Capsule:
    def __init__(self, index, rooms=None):
        self.index = index
        self.rooms = rooms if rooms else []
        self._update_constraints()
    
    def update(self, room_mapping):
        self.rooms = [room for room, capsule_index in room_mapping.items()
                           if self.index == capsule_index]
        self._update_constraints()
    
    def _update_constraints(self):
        self.constraints = [c for room in self.rooms
                              for c in room.constraints]

    def apply_constraints(self, global_constraints):
        self.constraints += global_constraints
        return self._is_valid()
    
    def _is_valid(self):
        ordered_constraints = sorted(self.constraints, key=lambda c: c.order)
        for constraint in ordered_constraints:
            valid, state = constraint.is_valid(self.index, self.rooms)
            if not valid:
                logger.debug((valid, [str(a) for a in state], constraint))
                return valid, state
        return True, []

class CapsulesManager:
    max_tries_count = 20
    max_fixes_count = 2000

    def __init__(self, rooms, capsules_count, global_constraints, existing_room_mapping=None):
        self.global_constraints = global_constraints

        self.rooms = rooms
        self.room_mapping = {room: None for room in self.rooms.values()}

        self.capsules_count = capsules_count

        for try_count in range(CapsulesManager.max_tries_count):
            logger.info(f'\nStart building capsules, attempt {try_count+1}/{CapsulesManager.max_tries_count}')
            succeded = self.build_capsules(existing_room_mapping)
            if succeded:
                return
        
        raise RuntimeError("Reached maximum try attempts")

    def randomize_room_mapping(self):
        self.allocate_rooms_randomly(self.rooms.keys())
    
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
            
        for fix_count in range(CapsulesManager.max_fixes_count):
            logger.info(f'Attempting to fix capsules, ({fix_count+1}/{CapsulesManager.max_fixes_count})')
            needed_fixing = self.fix_capsules()
            if not needed_fixing:
                return True
        
        if needed_fixing:
            return False
  
    def fix_capsules(self):
        '''
        Apply global constaints and try to fix invalid capsules
        Return boolean if needed fixing
        '''
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
        # The action only influence room_mapping,
        # therefore we must update the capsules
        action.do(self.room_mapping)
        self.update_capsules()
    
    def update_capsules(self):
        for capsule in self.capsules.values():
            capsule.update(self.room_mapping)
    
    def get_capsules(self):
        capsules = [[room.index for room in capsule.rooms] for capsule in self.capsules.values()]
        capsules.sort(key=lambda x:len(x) and x[0])
        return capsules

    def print_room_mapping(self):
        print({room.index: capsule for room, capsule in self.room_mapping.items()})
