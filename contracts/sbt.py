"""
TezCard SBT contract 
In TezCard world every thing maybe a SBT 

TODO: rename to Orgnazition and mixin the logic of rank operation 
close rank 
"""
import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

t_rank_variables = sp.TVariant(
    fixed_rank = sp.TRecord(
        threhold_score=sp.TNat
    ),
    time_elapsed = sp.TRecord(
        threhold_block_level=sp.TNat,
        threhold_member_count = sp.TNat
    )
)
t_rank_record = sp.TRecord(
    orgnazition_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weight=sp.TList(sp.TNat),
    open=sp.TBool,
    variable=t_rank_variables,
).layout(("orgnazition_id", ("factors", ("weight", ("open", "variable")))))

# define the role-based authorization control like normal web2 application
class RBAC:
    pass

class Organization(sp.Contract,
                    FA2.FA2,
                    FA2.MintFungible,
                    FA2.Fa2Nft,
                    FA2.OnchainviewBalanceOf):
    def __init__(self, evaluation_address, metadata):
        FA2.Fa2Nft.__init__(self, metadata, policy = FA2.NoTransfer())
        # # manager address list
        # evaluation contract address
        # contract metadata
        self.init(
            NFT0 = metadata,
            evaluation_address = evaluation_address,
            power_mint_address_set = sp.TSet(sp.TAddress), # own sbt address list
            owner_address_map = sp.big_map({}, tkey = sp.TAddress,
                                                tvalue = sp.utils.metadata_of_url("http://example.com"))
        )

#         NFT0 = FA2.make_metadata(
#             name     = "SBT MetaData",
#             decimals = 0,
#             symbol   = "EFA2" )

    @sp.entry_point
    def on_create_rank(self):
        # check permissions
        self.verify(self.sender == self.data.evaluation_address)
        pass


    @sp.entry_point
    def on_join_rank(self):
        # check permissions
        self.verify(self.sender == self.data.evaluation_address)
        pass

    @sp.entry_point
    def on_check_join(self):
        # check permissions
        self.verify(self.sender == self.data.evaluation_address)
        pass

    @sp.entry_point
    def on_receive_factor(self, params):
        sp.set_type(params, sp.TAddress)
        # check permissions
        self.verify(self.sender == self.data.evaluation_address)
        self.data.power_mint_address_set.add(params)

    @sp.entry_point
    def list_participate(self, params):
		sp.set_type(params, sp.TRecord(
			rank_id = sp.TAddress,
		))

    @sp.entry_point
	def list_rank(self, params):
		sp.set_type(params, sp.TRecord(
			limit = sp.TNat,
			offset = sp.TNat,
		))

    @sp.entry_point
    def mint(self, batch):
        # check can or cannot mint
        self.verify(self.data.power_mint_address_set.contains(self.sender))
        self.verify(! self.data.owner_address_map.keys().contains(self.sender))

        example_fa2_nft.mint(
            [
                sp.record(
                    to_  = self.sender, # Who will receive the original mint
                    metadata = self.data.NFT0
                )
            ]
        ).run(sender = self.sender)

        # storage already mint
        self.data.owner_address_map[self.sender] = self.data.NFT0

    @sp.entry_point
    def get_balance_of(self):
        self.data.owner_address_map.keys().contains(self.sender)
