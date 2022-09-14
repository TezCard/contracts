import smartpy as sp

SBT = sp.io.import_script_from_url("file:contracts/organization.py")
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

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


#
# t_rank_variables = sp.TVariant(
#     fixed_rank=sp.TRecord(
#         threshold_score=sp.TNat
#     ),
#     time_elapsed=sp.TRecord(
#         threshold_block_level=sp.TNat,
#         threshold_member_count=sp.TNat
#     )
# )

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
        self.initial_organization_contract = SBT.Organization()

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
                madels = sp.big_map({}, tkey=sp.TNat, tvalue=SBT.t_madel_record),
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
        with sp.for_("item", my_joined.items()) as item:
            result.push(item.value)
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


@sp.add_test(name="AddFactorTest")
def test_add_factor():
    pass
    sc = sp.test_scenario()
    alice = sp.test_account("Alice1")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.add_factor(
        sp.record(
            owner=bob.address,
            name=sp.bytes("0x12"),
            address=sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm"),
            once=sp.bool(False)
        )
    ).run(source=alice.address)
    sc.verify(factory.data.next_factor_id == sp.nat(2))
    sc.verify(factory.data.factors.contains(sp.nat(1)))
    sc.verify(factory.data.factor_addresses.contains(sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")))


@sp.add_test(name="PauseFactorTest")
def test_pause_factor():
    pass
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.add_factor(
        sp.record(
            owner=bob.address,
            name=sp.bytes("0x12"),
            address=sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm"),
            once=sp.bool(False)
        )
    ).run(source=alice.address)
    sc.verify(factory.data.next_factor_id == sp.nat(2))
    sc.verify(factory.data.factors.contains(sp.nat(1)))
    sc.verify(factory.data.factor_addresses.contains(sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")))

    factory.pause_factor(
        sp.record(
            factor_id=sp.nat(1),
            pause=sp.bool(True)
        )
    )
    sc.verify(factory.data.factors.contains(sp.nat(1)))


@sp.add_test(name="ListFactorTest")
def test_list_factor():
    pass
    sc = sp.test_scenario()
    alice = sp.test_account("Alice3")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.add_factor(
        sp.record(
            owner=bob.address,
            name=sp.bytes("0x12"),
            address=sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm"),
            once=sp.bool(False)
        )
    ).run(source=alice.address)
    sc.show(factory.list_factors(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ))


@sp.add_test(name="ListOrganizationTest")
def test_list_Organization():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice2")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.create_organization(
        sp.record(
            name=sp.bytes("0x01"),
            logo=sp.bytes("0x12"),
            decr=sp.bytes("0x13")
        )
    ).run(source=alice.address)

    sc.show(factory.list_organization(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ))


@sp.add_test(name="CreateOrganizationTest")
def test_create_organization():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.create_organization(
        sp.record(
            name=sp.bytes("0x01"),
            logo=sp.bytes("0x12"),
            decr=sp.bytes("0x13")
        )
    ).run(source=alice.address)
    sc.verify(factory.data.next_organization_id == sp.nat(2))
    sc.verify(factory.data.organizations.contains(sp.nat(1)))
    sc.verify(factory.data.organization_names.contains(sp.bytes("0x01")))


@sp.add_test(name="ListMyCreatedOrganizationTest")
def test_my_created_organization():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice2")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.create_organization(
        sp.record(
            name=sp.bytes("0x01"),
            logo=sp.bytes("0x12"),
            decr=sp.bytes("0x13")
        )
    ).run(source=alice.address)

    sc.show(factory.list_my_created_organization(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ).run(source=alice.address))


@sp.add_test(name="ListMyJoinedOrganizationTest")
def test_my_joined_organization():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice2")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.create_organization(
        sp.record(
            name=sp.bytes("0x01"),
            logo=sp.bytes("0x12"),
            decr=sp.bytes("0x13")
        )
    ).run(source=alice.address)

    sc.show(factory.list_my_join_organization(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ).run(source=alice.address))


sp.add_compilation_target("TezCard-Main",
                          OrganizationFactory(sp.record(admin=sp.address("tz1TZBoXYVy26eaBFbTXvbQXVtZc9SdNgedB"))))