import smartpy as sp

SBT = sp.io.import_script_from_url("file://organization.py")
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
    decr=sp.TBytes
).layout(("id", ("address", ("name", ("logo", "decr")))))

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

class OrganizationFactory(FA2.Admin, sp.Contract):
    def __init__(self, administrator):
        FA2.Admin.__init__(self, administrator)
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
            # # record the organizition
            # my_created_organizations=sp.big_map(
            #     tkey=sp.TNat,
            #     tvalue=sp.TUnit
            # ),
            #
            # my_joined_organizations=sp.big_map(
            #     tkey=sp.TAddress,
            #     tvalue=sp.TUnit
            # ),
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

    @sp.entry_point
    def create_organization(self, params):
        """
        create a new organization
        """
        sp.set_type(params, t_organization_params)
        sp.verify(self.is_administrator(sp.source), "only administrator can create a new organization")
        sp.verify(self.data.organization_names.contains(params.name), "Organization is exists")
        address = sp.self_address

        # contract = SBT.Organization(factory_address=address, administrator=self.data.admin, name=params.name, description=params.decr, logo=params.logo) # FIXME: maybe failed
        # organization_address = sp.create_contract(contract=contract)
        organization_address = sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")
        organization_id = self.data.next_organization_id
        # storage
        self.data.next_organization_id += 1
        self.data.organization_names[params.name] = sp.unit
        record = sp.record(
            id=organization_id,
            address=organization_address,
            name=params.name,
            logo=params.logo,
            decr=params.decr
        )
        self.data.organizations[organization_id] = record

    @sp.entry_point
    def add_factor(self, params):
        """
        add a new factor
        """
        sp.set_type(params, t_add_factor_params)
        sp.verify(self.is_administrator(sp.source), "only administrator can create a new factor")
        sp.verify(self.data.factor_addresses.contains(params.address), "factor has already add")
        factor_id = self.data.next_factor_id
        # storage
        self.data.next_factor_id += 1
        self.data.factor_addresses[params.address] = sp.unit
        factor = sp.record(
            owner=params.owner,
            address=params.address,
            pause=sp.bool(False),
            name=params.name,
            once=params.once
        )
        self.data.factors[factor_id] = factor

    @sp.offchain_view()
    # @sp.entry_point
    def pause_factor(self, params):
        """
        pause an factor
        """
        sp.set_type(params, t_pause_factor_params)
        sp.verify(self.is_administrator(sp.source), "only administrator can pause a new factor")
        sp.verify(self.data.factors.contains(params.factor_id), "factor_id not exists")
        self.data.factors[params.factor_id].pause = sp.bool(params.pause)

    @sp.offchain_view()
    def list_factors(self, params):
        """
        list the factor by page
        """
        sp.set_type(params, t_list_factor_params)
        sp.verify(params.offset < self.data.next_factor_id, "offset is overflow")
        end = params.limit if params.limit + params.offset < self.data.next_factor_id else self.data.next_factor_id
        index = params.offset
        result = sp.list()
        with sp.while_(index < end):
            result.push(self.data.factors[index])
            index += 1
        sp.set_result_type(sp.TList(t_factor_record))
        sp.result(result)

    @sp.offchain_view()
    def list_organization(self, params):
        """
        list the organizations by page
        """
        sp.set_type(params, t_list_organizations_params)
        sp.verify(params.offset < self.data.next_organization_id, "offset is overflow")
        end = params.limit if params.limit + params.offset < self.data.next_organization_id else self.data.next_organization_id
        index = params.offset
        result = sp.list()
        with sp.while_(index < end):
            result.push(self.data.organizations[index])
            index += 1
        sp.set_result_type(sp.TList(t_organization_record))
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
    ).run(source=bob.address)
    sc.verify(factory.data.next_factor_id == sp.nat(2))
    sp.verify(factory.data.factors.contains(sp.nat(1)))
    sp.verify(factory.data.factor_addresses.contains(sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")))


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
    ).run(source=bob.address)
    sc.verify(factory.data.next_factor_id == sp.nat(2))
    sp.verify(factory.data.factors.contains(sp.nat(1)))
    sp.verify(factory.data.factor_addresses.contains(sp.address("tz1aTgF2c3vyrk2Mko1yzkJQGAnqUeDapxxm")))

    factory.pause_factor(
        sp.record(
            factor_id=sp.nat(1),
            pause=sp.bool(True)
        )
    ).run(source=bob.address)
    sp.verify(factory.data.factors[sp.nat(1)])


@sp.add_test(name="ListFactorTest")
def test_list_factor():
    pass
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.list_factors(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ).run(source=bob.address)


@sp.add_test(name="ListOrganizationTest")
def test_list_Organization():
    sc = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    factory = OrganizationFactory(administrator=alice.address)
    sc += factory
    factory.list_organization(
        sp.record(
            offset=sp.nat(1),
            limit=sp.nat(10)
        )
    ).run(source=bob.address)


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
    ).run(source=bob.address)
    sc.verify(factory.data.next_organization_id == sp.nat(2))
    sp.verify(factory.data.organizations.contains(sp.nat(1)))
    sp.verify(factory.data.organization_names.contains(sp.bytes("0x01")))


sp.add_compilation_target("TezCard-Main",
                          OrganizationFactory(sp.record(admin=sp.address("tz1TZBoXYVy26eaBFbTXvbQXVtZc9SdNgedB"))))