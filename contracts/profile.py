import smartpy as sp

# Profile Contract to describe the user profile in Organization


class Profile(sp.Contract):
    """
    simple on-chain profile for every Organization member 

    if some user has any SBT in any Organization then the user could build their 
    own profile and also shared between any organization
    """

    def __init__(self):
        pass

    @sp.entry_point
    def create_profile(self, params):
        pass

    @sp.entry_point
    def update_thumb(self, params):
        pass

    @sp.entry_point
    def remove_skills(self, params):
        pass

    @sp.entry_point
    def add_skills(self, params):
        pass

