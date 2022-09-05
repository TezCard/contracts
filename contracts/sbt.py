"""
TezCard SBT contract 
In TezCard world every thing maybe a SBT 

TODO: rename to Organization and mixin the logic of rank operation
close rank 
"""
import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

t_rank_variables = sp.TVariant(
    fixed_rank=sp.TRecord(
        threshold_score=sp.TNat
    ),
    time_elapsed=sp.TRecord(
        threshold_block_level=sp.TNat,
        threshold_member_count=sp.TNat
    )
)
t_rank_record = sp.TRecord(
    rank_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weights=sp.TList(sp.TNat),
    open=sp.TBool,
    variable=t_rank_variables,
    pause=sp.TBool
).layout(("rank_id", ("factors", ("weights", ("open", ("variable", "pause"))))))

t_rank_joins_record = sp.TRecord(
    rank_id=sp.TNat,
    join_users=sp.TSet(sp.TAddress),
    win_users=sp.TSet(sp.TAddress),
    minted_users=sp.TSet(sp.TAddress)
).layout(("rank_id", ("join_users", "win_users")))

t_list_params = sp.TRecord(
    type=sp.TNat,  # 1=join, 2=win, 3=mint
    offset=sp.TNat,
    limit=sp.TNat
).layout(("offset", "limit"))

t_list_rank_params = sp.TRecord(
    rank_id=sp.TNat,
    type=sp.TNat,  # 1=join, 2=win, 3=mint
    offset=sp.TNat,
    limit=sp.TNat
).layout(("rank_id", ("offset", "limit")))


# define the role-based authorization control like normal web2 application
class RBAC:
    pass


class Organization(sp.Contract,
                   FA2.FA2,
                   FA2.MintFungible,
                   FA2.Fa2Nft,
                   FA2.OnchainviewBalanceOf):
    def __init__(self, evaluation_address, managers, metadata):
        FA2.Fa2Nft.__init__(self, metadata, policy=FA2.NoTransfer())
        sp.set_type(evaluation_address, sp.TAddress)
        sp.set_type(managers, sp.TList(sp.TAddress))
        # # manager address list
        # evaluation contract address
        # contract metadata
        self.init(
            NFT0=metadata,
            evaluation_address=evaluation_address,
            t_rank_joins_map=sp.big_map(tkey=sp.TNat, tvalue=t_rank_joins_record),
            # organization join address map
            #             t_joins = sp.big_map(tkey = sp.TAddress, tvalue = sp.TUnit),
            # organization join and win address map
            #             t_wins = sp.big_map(tkey = sp.TAddress, tvalue = sp.TUnit),
            t_rank_record_map=sp.big_map(tkey == sp.TNat, tvalue=t_rank_record),
            managers=managers,
            # storage already mint address
            owner_address_map=sp.big_map({}, tkey=sp.TAddress,
                                         tvalue=sp.utils.metadata_of_url("http://example.com"))
        )

        #         NFT0 = FA2.make_metadata(
        #             name     = "SBT MetaData",
        #             decimals = 0,
        #             symbol   = "EFA2" )

        @sp.entry_point
        def on_create_organization(self, params):
            # check permissions
            self.verify(sp.sender == self.data.evaluation_address)
            self.set_type(params, sp.TList(sp.TAddress))
            self.data.managers = params

        @sp.entry_point
        def on_create_rank(self, params):
            # check permissions
            self.verify(sp.sender == self.data.evaluation_address)
            sp.set_type(params, t_rank_record)
            sp.verify(self.data.t_rank_record_map.contains(params.rank_id), "rank not exists")
            # storage
            self.data.t_rank_record_map[params.rank_id] = params

        @sp.entry_point
        def on_join_rank(self, user, rank_id):
            sp.set_type(user, sp.TAddress)
            sp.set_type(rank_id, sp.TNat)
            # only evaluation can call
            self.verify(sp.sender == self.data.evaluation_address, "only evaluation can call")
            # check rank_id exists
            self.verify(self.t_rank_address.contains(rank_id), "rank is not exists")
            # TODO whether or not check rank is open or close
            # storage
            self.data.t_rank_joins_map[rank_id].join_users.add(user)

        #         self.data.t_joins[user] = sp.none

        @sp.entry_point
        def on_check_join(self):
            # check permissions
            self.verify(sp.sender == self.data.evaluation_address)
            pass

        @sp.entry_point
        def on_receive_factor(self, params):
            sp.set_type(params, sp.TAddress)
            # check permissions
            self.verify(sp.sender == self.data.evaluation_address)

        @sp.offchain_view()
        @sp.entry_point
        def list_rank(self, params):
            sp.set_type(params, t_list_rank_params)
            # check rank exist
            sp.verify(self.data.t_rank_joins_map.contains(params.rank_id), "rank not exist")

            list_users = sp.TList(sp.TAddress)
            if t_list_rank_params.type == 1:
                list_users = self.data.t_rank_joins_map[rank_id].join_users
            elif t_list_rank_params.type == 2:
                list_users = self.data.t_rank_joins_map[rank_id].win_users
            else:
                list_users = self.data.t_rank_joins_map[rank_id].minted_users
            len = sp.len(list_users)
            sp.verify(params.offset < len, "offset is overflow")
            end = params.limit if params.limit + params.offset < len else len
            index = params.offset
            result = sp.TList()
            with sp.while_(index < end):
                result.push(list_users[index])
            index += 1
            sp.set_result_type(sp.TList(sp.TAddress))
            sp.result(result)

    @sp.entry_point
    def list_participant(self, params):
        sp.set_type(params, t_list_params)
        # TODO check params.type is invalid
        participants = sp.TList(sp.TAddress)
        if t_list_rank_params.type == 1:
            participants = sp.TSet(sp.TAddress)
            for x in self.data.t_rank_joins_map.keys():
                participants.add(self.data.t_rank_joins_map[x].join_users)
        elif t_list_rank_params.type == 2:
            participants = sp.TSet(sp.TAddress)
            for x in self.data.t_rank_joins_map.keys():
                participants.add(self.data.t_rank_joins_map[x].win_users)

        else:
            participants = sp.TSet(sp.TAddress)
            for x in self.data.t_rank_joins_map.keys():
                participants.add(self.data.t_rank_joins_map[x].minted_users)

        len = sp.len(participants)
        sp.verify(params.offset < len, "offset is overflow")
        end = params.limit if params.limit + params.offset < len else len
        index = params.offset
        result = sp.TList()
        with sp.while_(index < end):
            result.push(participants[index])
        index += 1
        sp.set_result_type(sp.TList(sp.TAddress))
        sp.result(result)

    @sp.entry_point
    def mint(self, param):
        sp.set_type(param, sp.TNat)
        # check rank_id exist
        self.verify(self.data.t_rank_joins_map.contains(param), "rank not exist")
        # check can or cannot mint
        tag = sp.bool(False)
        for x in self.data.t_rank_joins_map.keys():
            if self.data.t_rank_joins_map[x].win_users.contains(sp.sender):
                tag = sp.bool(True)
        self.verify(tag, "you have no permissions to mint")
        self.verify(not self.data.owner_address_map.keys().contains(sp.sender), "already mint, cannot mint again")

        example_fa2_nft.mint(
            [
                sp.record(
                    to_=sp.sender,  # Who will receive the original mint
                    metadata=self.data.NFT0
                )
            ]
        ).run(sender=sp.sender)

        # TODO calculate top

        # storage already mint
        self.data.owner_address_map[sp.sender] = self.data.NFT0
        self.data.t_rank_joins_map[param].minted_users.add(sp.sender)

    @sp.entry_point
    def get_balance_of(self):
        sp.set_result_type(sp.TNat)
        if self.data.owner_address_map.keys().contains(sp.sender):
            sp.result(1)
        else:
            sp.result(0)
