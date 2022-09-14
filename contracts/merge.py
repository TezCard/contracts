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


t_organization_params = sp.TRecord(
    name=sp.TBytes,
    logo=sp.TBytes,
    decr=sp.TBytes
).layout(("name", ("logo", "decr")))

t_organization_record = sp.TRecord(
    id=sp.TNat,
    address=sp.TAddress,
    name=sp.TBytes,
    logo=sp.TBytes,
    decr=sp.TBytes,
    timestamp=sp.TTimestamp
).layout(("id", ("address", ("name", ("logo", ("decr", "timestamp"))))))

t_add_factor_params = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TBytes,
    address=sp.TAddress,
    once=sp.TBool
).layout(("owner", ("name", ("address", "once"))))

t_factor_record = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TBytes,
    address=sp.TAddress,
    pause=sp.TBool,
    once=sp.TBool
).layout(("owner", ("name", ("address", ("pause", "once")))))

t_pause_factor_params = sp.TRecord(
    factor_id=sp.TNat,
    pause=sp.TBool
).layout(("factor_id", "pause"))

t_list_factor_params = sp.TRecord(
    offset=sp.TNat,
    limit=sp.TNat
).layout(("offset", "limit"))

t_list_organizations_params = sp.TRecord(
    offset=sp.TNat,
    limit=sp.TNat
).layout(("offset", "limit"))

class Organization(FA2.Fa2Nft,
                   FA2.OffchainviewTokenMetadata,
                   FA2.Admin,
                   FA2.OnchainviewBalanceOf):

    def __init__(self):
        FA2.Fa2Nft.__init__(self, metadata=sp.big_map(l=None, tkey=sp.TString, tvalue=sp.TBytes))
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

    @sp.offchain_view()
    def madel_rank_details(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        sp.verify(self.data.madels.contains(rank_id), "madel rank is not exists")
        sp.result(self.data.madels[rank_id])

    @sp.offchain_view()
    def list_my_participated_ranks(self):
        result = sp.compute(sp.list(l=[], t=sp.TNat))
        with sp.for_("item", self.data.my_participated_ranks[sp.source].keys()) as item:
            result.push(item)
        sp.result(result)

    @sp.offchain_view()
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

    @sp.offchain_view()
    def is_madel_rank_open(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        with sp.if_(self.data.madels.contains(rank_id)):
            sp.result(
                ~self.data.madels[rank_id].end
            )
        with sp.else_():
            sp.result(sp.bool(False))

    @sp.onchain_view()
    def is_madel_rank_open(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        with sp.if_(self.data.madels.contains(rank_id)):
            sp.result(
                ~self.data.madels[rank_id].end
            )
        with sp.else_():
            sp.result(sp.bool(False))

    @sp.offchain_view()
    def organization_details(self):
        sp.result(
            sp.record(
                name=self.data.name,
                description=self.data.description,
                logo=self.data.logo
            )
        )


class OrganizationFactory(sp.Contract):
    def __init__(self, administrator):
        # FA2.Admin.__init__(self, administrator)
        self.update_initial_storage(
            # organizations
            next_organization_id=sp.nat(1),
            organizations=sp.big_map(
                tkey=sp.TNat,
                tvalue=t_organization_record
            ),
            organization_names=sp.big_map(
                tkey=sp.TBytes,
                tvalue=sp.TUnit
            ),
            # record the organizition
            my_created_organizations=sp.big_map({},
                                                tkey=sp.TAddress,
                                                tvalue=sp.TMap(sp.TNat, t_organization_record)
                                                ),
            #
            my_joined_organizations=sp.big_map({},
                                               tkey=sp.TAddress,
                                               tvalue=sp.TMap(sp.TNat, t_organization_record)
                                               ),
            # factors
            next_factor_id=sp.nat(1),
            factors=sp.big_map(
                tkey=sp.TNat,
                tvalue=t_factor_record
            ),
            factor_addresses=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TUnit
            )
        )
        self.initial_organization_contract = Organization()

    def if_organization_created(self, name):
        return self.data.organization_names.contains(name)

    @sp.entry_point
    def create_organization(self, params):
        """
        create a new organization
        any one has permission to create
        """
        sp.set_type(params, t_organization_params)
        # sp.verify(self.is_administrator(sp.source), "only administrator can create a new organization")
        sp.verify(~self.if_organization_created(params.name), "Organization is exists")
        address = sp.self_address

        # contract = SBT.Organization(factory_address=address, administrator=self.data.admin, name=params.name, description=params.decr, logo=params.logo) # FIXME: maybe failed
        #organization_address = sp.create_contract(contract=contract)
        organization_address = sp.create_contract(
            storage=sp.record(
                administrator=sp.source,
                description=params.decr,
                ended_madel_ranks = sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
                factory_address=sp.self_address,
                last_token_id=sp.nat(0),
                ledger=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TAddress),
                logo=params.logo,
                madels = sp.big_map({}, tkey=sp.TNat, tvalue=t_madel_record),
                members = sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TNat),
                metadata = sp.big_map({}, tkey=sp.TString, tvalue=sp.TBytes),
                my_madels = sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TNat)),
                my_participated_ranks = sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TMap(sp.TNat, sp.TUnit)),
                name = params.name,
                next_madel_id = sp.nat(1),
                opened_madel_ranks = sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
                operators = sp.big_map({}, tkey=FA2.t_operator_permission, tvalue=sp.TUnit),
                started_madel_ranks = sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
                token_metadata = sp.big_map({}, tkey=sp.TNat, tvalue=sp.TRecord(
                    token_id = sp.TNat, 
                    token_info = sp.TMap(sp.TString, sp.TBytes)
                ))
            ),
            contract=self.initial_organization_contract
        )
        #organization_address = sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")
        organization_id = sp.compute(self.data.next_organization_id)

        self.data.organization_names[params.name] = sp.unit
        timeStamp = sp.now
        record = sp.record(
            id=organization_id,
            address=organization_address,
            name=params.name,
            logo=params.logo,
            decr=params.decr,
            timestamp=timeStamp
        )
        self.data.organizations[organization_id] = record
        # storage
        self.data.next_organization_id += 1
        self.data.my_created_organizations[sp.sender][organization_id] = record
        self.data.my_joined_organizations[sp.sender][organization_id] = record

    def if_factory_created(self, address):
        return self.data.factor_addresses.contains(address)

    @sp.entry_point
    def add_factor(self, params):
        """
        add a new factor
        """
        sp.set_type(params, t_add_factor_params)
        # sp.verify(self.is_administrator(sp.source), "only administrator can create a new factor")
        sp.verify(~self.if_factory_created(params.address), "factor has already add")
        factor_id = sp.compute(self.data.next_factor_id)

        self.data.factor_addresses[params.address] = sp.unit
        factor = sp.record(
            owner=params.owner,
            address=params.address,
            pause=sp.bool(False),
            name=params.name,
            once=params.once
        )
        self.data.factors[factor_id] = factor
        # storage
        self.data.next_factor_id += 1

    def if_factor_exist(self, factor_id):
        return self.data.factors.contains(factor_id)

    @sp.offchain_view()
    def pause_factor(self, params):
        """
        pause an factor
        """
        sp.set_type(params, t_pause_factor_params)
        # sp.verify(self.is_administrator(sp.source), "only administrator can pause a new factor")
        sp.verify(self.if_factor_exist(params.factor_id), "factor_id not exists")
        self.data.factors[params.factor_id].pause = params.pause

    def check_page_factor_offset_limit(self, offset):
        return offset < self.data.next_factor_id

    @sp.offchain_view()
    def list_factors(self, params):
        """
        list the factor by page
        """
        sp.set_type(params, t_list_factor_params)
        sp.verify(self.check_page_factor_offset_limit(params.offset), "offset is overflow")
        with sp.if_(params.limit + params.offset < self.data.next_factor_id):
            end = params.limit
        with sp.else_():
            end = self.data.next_factor_id
        index = params.offset
        result = sp.compute(sp.list([]))
        with sp.while_(index < end):
            result.push(self.data.factors[index])
            index += 1
        # sp.set_result_type(sp.TList(t_factor_record))
        sp.result(result)

    def check_page_organization_offset_limit(self, offset):
        return offset < self.data.next_organization_id

    @sp.offchain_view()
    def list_organization(self, params):
        """
        list the organizations by page
        """
        sp.set_type(params, t_list_organizations_params)
        sp.verify(self.check_page_organization_offset_limit(params.offset), "offset is overflow")
        with sp.if_(params.limit + params.offset < self.data.next_organization_id):
            end = params.limit
        with sp.else_():
            end = self.data.next_organization_id
        index = params.offset
        result = sp.compute(sp.list([]))
        with sp.while_(index < end):
            result.push(self.data.organizations[index])
            index += 1

        # sp.set_result_type(sp.TList(t_organization_record))
        sp.result(result)

    def if_has_created_organization(self, address):
        return self.data.my_created_organizations.contains(address)

    @sp.offchain_view()
    def list_my_created_organization(self, params):
        """
        list the organizations by page
        """
        sp.set_type(params, t_list_organizations_params)
        sp.verify(self.if_has_created_organization(sp.sender), "address hasn't created organization")
        my_created = self.data.my_created_organizations[sp.sender]

        result = sp.compute(sp.list([]))
        with sp.for_("item", my_created.items()) as item:
            result.push(item.value)
        sp.result(result)

    def if_has_joined_organization(self, address):
        return self.data.my_joined_organizations.contains(address)

    @sp.offchain_view()
    def list_my_join_organization(self, params):
        """
        list the organizations by page
        """
        sp.set_type(params, t_list_organizations_params)
        sp.verify(self.if_has_joined_organization(sp.sender), "address hasn't created organization")
        my_joined = self.data.my_joined_organizations[sp.sender]
        result = sp.compute(sp.list([]))
        with sp.for_("id", my_joined.keys()) as organ:
            result.push(my_joined[organ])
        sp.result(result)

    # @sp.entry_point
    # def on_rank_created(self, params):
    #     pass
    #
    # @sp.entry_point
    # def on_rank_open(self, params):
    #     pass
    #
    # @sp.entry_point
    # def on_rank_closed(self, params):
    #     pass
    #
    # @sp.entry_point
    # def on_member_join_rank(self, params):
    #     """
    #     someone join the rank
    #     """
    #     pass
    #
    # @sp.entry_point
    # def on_member_leave_rank(self, params):
    #     pass
    #
    # @sp.entry_point
    # def on_member_mint(self, params):
    #     pass
    #
    # @sp.entry_point
    # def on_receive_score(self, params):
    #     pass


sp.add_compilation_target("TezCard-Main",
                          OrganizationFactory(sp.record(admin=sp.address("tz1TZBoXYVy26eaBFbTXvbQXVtZc9SdNgedB"))))