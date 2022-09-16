"""
TezCard Soul Bounded Token
"""
import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

#########
# Types #
#########

t_madel_parameter = sp.TVariant(
    fixed_score=sp.TRecord(
        threshold_score_limit=sp.TNat,
        threshold_member_limit=sp.TOption(sp.TNat)
    ),
    time_elapsed=sp.TRecord(
        threshold_block_level=sp.TNat,
        threshold_member_limit=sp.TNat
    )
)

t_madel_record = sp.TRecord(
    name=sp.TBytes,
    description=sp.TBytes,
    factors=sp.TMap(sp.TAddress, sp.TNat),
    open=sp.TBool,
    end=sp.TBool,
    parameter=t_madel_parameter,
    candidates=sp.TMap(sp.TAddress, sp.TNat),
    winners=sp.TList(sp.TAddress),
    max_score=sp.TNat,
    min_score=sp.TNat, 
)


t_my_madel_record = sp.TRecord(
    block_level=sp.TNat,
    score=sp.TNat,
    soul_id=sp.TNat,
)

t_organization_result = sp.TRecord(
    name=sp.TBytes,
    description=sp.TBytes,
    logo=sp.TBytes
).layout(("name", ("description", "logo")))

t_soul_profile_params=sp.TRecord(
    name=sp.TBytes,
    introduce=sp.TBytes,
    logo=sp.TBytes
)

t_create_madel_rank_params = sp.TRecord(
    name=sp.TBytes,
    description=sp.TBytes,
    factors=sp.TMap(sp.TAddress, sp.TNat),
    parameter=t_madel_parameter,
)

t_open_madel_rank_params = sp.TRecord(
    rank_id=sp.TNat
)

t_my_madel_details = sp.TRecord(
    madel_id=sp.TNat,
    name=sp.TBytes,
    description=sp.TBytes,
    block_level=sp.TNat
)


t_factor_receive_score_param = sp.TRecord(
    rank_id=sp.TNat,
    address=sp.TAddress,
    score=sp.TNat
)

t_join_madel_rank_param = sp.TRecord(
    rank_id=sp.TNat
)

# t_list_madel_ranks_params = sp.TVariant(
#     opened=sp.TRecord(

#     ),
#     ended=sp.TRecord(

#     ),
#     started=sp.TRecord(

#     ),
#     all=sp.TRecord(

#     )
# )

class Organization(FA2.Fa2Nft,
                   FA2.OffchainviewTokenMetadata,
                   FA2.Admin,
                   FA2.OnchainviewBalanceOf):

    def __init__(self):
        # A python dictionary that contains metadata entries
        metadata_base = {
            "name": "Organization contract",
            "version": "1.0.1",
            "description": "This implements FA2 (TZIP-012) using SmartPy.",
            "interfaces": ["TZIP-012", "TZIP-016"],
            "authors": ["SmartPy <https://smartpy.io/#contact>"],
            "homepage": "https://smartpy.io/ide?template=FA2.py",
            "source": {
                "tools": ["SmartPy"],
                "location": "https://gitlab.com/SmartPy/smartpy/-/raw/master/python/templates/FA2.py",
            },
            "permissions": {"receiver": "owner-no-hook", "sender": "owner-no-hook"},
            "views": [self.madel_rank_details, self.list_my_madels, self.list_my_participated_ranks]
        }
        # Helper method that builds the metadata and produces the JSON representation as an artifact.
        # self.init_metadata("example1", metadata)

        metadata=sp.big_map(l=None, tkey=sp.TString, tvalue=sp.TBytes)
        # metadata["views"] = [self.madel_rank_details, self.list_my_madels, self.list_my_participated_ranks]

        FA2.Fa2Nft.__init__(self, metadata=metadata, metadata_base=metadata_base)

        # metadata_base["permissions"]["operator"] = self.policy.name
        self.init_metadata("metadata_base", metadata_base)
        # FA2.FA2_core.__init__(self, config, metadata, paused=False, administrator=admin)

        self.update_initial_storage(
            factory_address=sp.address("KT1000000000000000000000000000000000"),
            name=sp.bytes("0x00"),
            description=sp.bytes("0x00"),
            logo=sp.bytes("0x00"),
            members=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TNat),
            next_madel_id=sp.nat(1),
            madels=sp.big_map({}, tkey=sp.TNat, tvalue=t_madel_record),
            opened_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            ended_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            started_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            my_participated_ranks=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TUnit)),
            my_madels=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TNat)),
        )
        FA2.Admin.__init__(self, sp.address("tz1000000000000000000000000000000000"))

    def if_soul_bottle_minted(self, address):
        return self.data.members.contains(address) 

    @sp.entry_point
    def create_soul_bottle(self, params):
        """
        create the soul bottle of a wallet
        """
        sp.set_type(params, t_soul_profile_params)
        sp.verify(~self.if_soul_bottle_minted(sp.source), "you have minted a soul bottle")
        token_id = sp.compute(self.data.last_token_id)
        metadata = sp.record(
            token_id = token_id,
            token_info = sp.map(l={
                "soul_name": params.name,
                "soul_introduce": params.introduce,
                "soul_logo": params.logo,
            }, tkey=sp.TString, tvalue=sp.TBytes)
        )
        self.data.token_metadata[token_id] = metadata
        self.data.ledger[token_id] = sp.source
        self.data.members[sp.source] = token_id
        self.data.last_token_id += 1
    
    @sp.entry_point
    def create_madel_rank(self, params):
        """
        create a new madel rank
        """
        sp.set_type(params, t_create_madel_rank_params)
        sp.verify(self.is_administrator(sp.source), "only administrator can create a new rank")
        rank_id = sp.compute(self.data.next_madel_id)

        # register on factor contract
        with sp.for_("factor", params.factors.keys()) as factor:
            sp.verify(params.factors[factor] > sp.nat(0), "factor weight must larger than zero")
            contract = sp.contract(
                sp.TRecord(
                    organization_address=sp.TAddress,
                    rank_id = sp.TNat,
                ),
                factor,
                "register"
            ).open_some("not a invalid factor contract")
            sp.transfer(
                sp.record(
                    organization_address=sp.self_address,
                    rank_id=rank_id,
                ),
                sp.tez(0),
                contract
            )
        
        # save in the organization records 
        record = sp.record(
            name=params.name,
            description=params.description,
            factors=params.factors,
            open=sp.bool(False),
            end=sp.bool(False),
            parameter=params.parameter,
            candidates=sp.map(l={}, tkey=sp.TAddress, tvalue=sp.TNat),
            winners=sp.list(l=[], t=sp.TAddress),
            max_score=sp.nat(0),
            min_score=sp.nat(0), 
        )
        self.data.madels[rank_id] = record

        # save in opened madel ranks
        self.data.opened_madel_ranks[rank_id] = sp.unit

        # update the last rank id
        self.data.next_madel_id += 1

    # @sp.offchain_view()
    # def list_madel_ranks(self, params):
    #     pass

    @sp.entry_point
    def start_madel_rank(self, params):
        """
        start a new madel rank
        """
        sp.set_type(params, t_open_madel_rank_params)
        sp.verify(self.is_administrator(sp.source), "only administrator can open a rank")
        sp.verify(self.data.opened_madel_ranks.contains(params.rank_id), "madel rank must be opened")
        # move to the started list
        self.data.started_madel_ranks[params.rank_id] = sp.unit
        self.data.madels[params.rank_id].open=sp.bool(True)
        del self.data.opened_madel_ranks[params.rank_id]

    # @sp.entry_point
    # def close_madel_ranks(self, params):
    #     pass

    @sp.entry_point
    def join_madel_rank(self, params):
        """
        let someone join the rank
        """
        sp.set_type(params, t_join_madel_rank_param)
        sp.verify(self.data.madels.contains(params.rank_id), "there no madel rank")
        sp.verify(~self.data.madels[params.rank_id].end, "madel rank is ended")
        sp.verify(self.data.madels[params.rank_id].open, "madel rank is not open now")
        self.data.madels[params.rank_id].candidates[sp.source] = sp.nat(0)

    # @sp.entry_point
    # def leave_madel_rank(self, params):
    #     pass

    # def is_madel_rank_time_elapsed(self, id):
    #     pass

    @sp.entry_point
    def receive_madel_rank_score(self, params):
        sp.set_type(params, t_factor_receive_score_param)
        sp.verify(self.data.madels.contains(params.rank_id), "there no madel rank")
        sp.verify(~self.data.madels[params.rank_id].end, "madel rank is ended")
        sp.verify(self.data.madels[params.rank_id].open, "madel rank is not open now")
        rank = self.data.madels[params.rank_id]
        with sp.if_(rank.parameter.is_variant("fixed_score")):
            parameter = rank.parameter.open_variant("fixed_score")
            self.calculate_fixed_score_rank(
                params.rank_id,
                sp.sender,
                params.address,
                params.score,
                parameter.threshold_score_limit,
                parameter.threshold_member_limit
            )

    def calculate_fixed_score_rank(
        self, 
        rank_id,
        factor_address, 
        wallet_address, 
        score, 
        score_limit, 
        memeber_limit):

        rank = self.data.madels[rank_id]
        candidate_score = rank.candidates[wallet_address]
        factor_weight = rank.factors[factor_address]
        winners = rank.winners
        now_score = sp.compute(
            score * factor_weight + candidate_score
        )
        # my_madels
        with sp.if_(memeber_limit.is_some()):
            limit = memeber_limit.open_some()
            with sp.if_(sp.len(winners) <= limit):
                with sp.if_(now_score > rank.max_score):
                    rank.max_score = now_score
                with sp.if_(now_score < rank.min_score):
                    rank.min_score = now_score
                with sp.if_(now_score >= score_limit):
                    winners.push(wallet_address)
            with sp.else_():
                rank.end = sp.bool(True)
            rank.winners=winners
            self.data.madels[rank_id] = rank
        with sp.else_():
            with sp.if_(now_score >= score_limit):
                winners.push(wallet_address)
            rank.winners=winners
            self.data.madels[rank_id] = rank

    @sp.onchain_view()
    def madel_rank_details(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        sp.verify(self.data.madels.contains(rank_id), "madel rank is not exists")
        sp.result(self.data.madels[rank_id])

    @sp.onchain_view()
    def list_my_participated_ranks(self):
        result = sp.compute(sp.list(l=[], t=sp.TNat))
        with sp.for_("item", self.data.my_participated_ranks[sp.source].keys()) as item:
            result.push(item)
        sp.result(result)

    @sp.onchain_view()
    def list_my_madels(self):
        result = sp.compute(sp.list(l=[], t=t_my_madel_details))
        my_madels = self.data.my_madels[sp.source]
        with sp.for_("item", my_madels.items()) as item:
            block_level = item.value
            madel = self.data.madels[item.key]
            result.push(
                sp.record(
                    madel_id=item.key,
                    name=madel.name,
                    description=madel.description,
                    block_level=block_level
                )
            )
        sp.result(result)

    # @sp.onchain_view()
    # def is_madel_rank_open(self, rank_id):
    #     sp.set_type(rank_id, sp.TNat)
    #     with sp.if_(self.data.madels.contains(rank_id)):
    #         sp.result(
    #             ~self.data.madels[rank_id].end
    #         )
    #     with sp.else_():
    #         sp.result(sp.bool(False))

    @sp.onchain_view()
    def is_madel_rank_open(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        with sp.if_(self.data.madels.contains(rank_id)):
            sp.result(
                ~self.data.madels[rank_id].end
            )
        with sp.else_():
            sp.result(sp.bool(False))

    @sp.onchain_view()
    def organization_details(self):
        sp.result(
            sp.record(
                name=self.data.name,
                description=self.data.description,
                logo=self.data.logo
            )
        )

    

class TestOrganizationFactory(sp.Contract):
    def __init__(self, administrator):
        self.init(
            administrator=administrator
        )

class TestFactorContract(sp.Contract):
    def __init__(self):
        self.init(
            ranks=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TUnit))
        )
    
    @sp.entry_point
    def register(self, params):
        sp.set_type(
            params,
            sp.TRecord(
                organization_address=sp.TAddress,
                rank_id = sp.TNat,
            )
        )
        with sp.if_(self.data.ranks.contains(params.organization_address)):
            self.data.ranks[params.organization_address][params.rank_id] = sp.unit
        with sp.else_():
            self.data.ranks[params.organization_address] = sp.map(
                l={
                    params.rank_id: sp.unit
                },
                tkey=sp.TNat,
                tvalue=sp.TUnit
            )
    
    @sp.entry_point
    def unregister(self, params):
       sp.set_type(
           params,
           sp.TRecord(
               organization=sp.TAddress,
               rank_id=sp.TNat
           )
       )
       sp.verify(self.data.ranks.contains(params.organization))
       sp.verify(self.data.ranks[params.organization].contains(params.rank_id))
       del self.data.ranks[params.organization][params.rank_id]

    @sp.entry_point
    def on_candidate_join(self, params):
        sp.set_type(
            params,
            sp.TRecord(
                organization=sp.TAddress,
                rank_id=sp.TNat,
                candidate=sp.TAddress
            )
        )

    @sp.entry_point
    def on_candidate_leave(self, params):
        sp.set_type(
            params,
            sp.TRecord(
                organization=sp.TAddress,
                rank_id=sp.TNat,
                candidate=sp.TAddress
            )
        )

@sp.add_test(name="MintSoulBottleTest")
def mint_soul_bottle_test():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = TestOrganizationFactory(administrator=alice.address)
    sc += factory
    organization = Organization()
    organization.update_initial_storage(
        factory_address=factory.address,
        administrator=alice.address,
        name=sp.bytes("0x01"),
        description=sp.bytes("0x02"),
        logo=sp.bytes("0x03"),
        members=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TNat),
        next_madel_id=sp.nat(1),
        madels=sp.big_map({}, tkey=sp.TNat, tvalue=t_madel_record),
        opened_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        ended_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        started_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        my_participated_ranks=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TUnit)),
        my_madels=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TNat)),
    )
    sc += organization
    sc.verify(organization.data.last_token_id == sp.nat(0))
    # success
    organization.create_soul_bottle(
        sp.record(
            name=sp.bytes("0x01"),
            introduce=sp.bytes("0x02"),
            logo=sp.bytes("0x03")
        )
    ).run(source=bob.address)
    sc.verify(organization.data.last_token_id == sp.nat(1))

@sp.add_test(name="CreateMadelRankTest")
def create_madel_rank_test():
    pass
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = TestOrganizationFactory(administrator=alice.address)
    factor = TestFactorContract()
    factor2 = TestFactorContract()
    sc += factory
    sc += factor
    sc += factor2
    organization = Organization()
    organization.update_initial_storage(
        factory_address=factory.address,
        administrator=alice.address,
        name=sp.bytes("0x01"),
        description=sp.bytes("0x02"),
        logo=sp.bytes("0x03"),
        members=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TNat),
        next_madel_id=sp.nat(1),
        madels=sp.big_map({}, tkey=sp.TNat, tvalue=t_madel_record),
        opened_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        ended_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        started_madel_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
        my_participated_ranks=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TUnit)),
        my_madels=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TNat)),
    )
    sc += organization
    sc.verify(organization.data.last_token_id == sp.nat(0))
    # create
    organization.create_madel_rank(
        sp.record(
            name=sp.bytes("0x01"),
            description=sp.bytes("0x02"),
            factors=sp.map(
                l={
                    factor.address: sp.nat(10),
                    factor2.address: sp.nat(20),
                },
                tkey=sp.TAddress,
                tvalue=sp.TNat
            ),
            parameter=sp.variant("fixed_score", sp.record(
                threshold_score_limit=sp.nat(20),
                threshold_member_limit=sp.none
            ))
        )
    ).run(source=alice.address)

    sc.verify(organization.data.next_madel_id == sp.nat(2))
    sc.verify(organization.data.opened_madel_ranks.contains(sp.nat(1)))
    sc.verify(factor.data.ranks.contains(organization.address))
    sc.verify(factor2.data.ranks.contains(organization.address))
    sc.verify(factor.data.ranks[organization.address].contains(sp.nat(1)))