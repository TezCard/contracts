"""
TezCard SBT contract 
In TezCard world every thing maybe a SBT 
"""
import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

class SBTMintPolicy(FA2.FA2,
                    FA2.MintFungible,
                    FA2.Fa2Nft,
                    FA2.OnchainviewBalanceOf):
    def __init__(self, metadata):
        # NFT0 = FA2.make_metadata(
        #     name     = "SBT MetaData",
        #     decimals = 0,
        #     symbol   = "EFA2" )

        FA2.Fa2Nft.__init__(self, metadata)
        # This adds two elements in the contract's data.
        self.data.sbt_rights = sp.big_map({}, tkey = sp.Address, tvalue = sp.TNat)

    def verify_tx_mint_permissions(self, sender):
        # Called each time a transaction is being looked at.
        # Called evaluation contract, the sender is permissions to mint sbt


    @sp.entry_point
    def mint(self, batch):
        # Anyone can mint
        self.verify_tx_mint_permissions(self.sender)

        example_fa2_nft.mint(
            [
                sp.record(
                    to_  = self.sender, # Who will receive the original mint
                    metadata = NFT0
                )
            ]
        ).run(sender = self.sender)

        # This adds two elements in the contract's data.
        self.update_initial_storage(x=self.sender, y=1)

    @sp.entry_point
    def get_balance_of(self):
        self.sbt_rights.contains(self.sender)
