import smartpy as sp

SBT = sp.io.import_script_from_url("file://.py")
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")


t_organization_params = sp.TRecord(
    managers=sp.TMap(sp.TAddress, sp.TUnit),
    name=sp.TBytes,
    logo=sp.TBytes,
    decr=sp.TString,
).layout(("managers", ("name", ("logo", "decr"))))

t_organization_record = sp.TRecord(
    id=sp.TNat,
    address=sp.TAddress,
).layout(("id", "address"))

t_add_factor_params = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TString,
    address=sp.TAddress,
    once=sp.TBool
).layout(("owner", ("name", ("address", "once"))))

t_factor_record = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TString,
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

t_rank_variables = sp.TVariant(
    fixed_rank=sp.TRecord(
        threshold_score=sp.TNat
    ),
    time_elapsed=sp.TRecord(
        threshold_block_level=sp.TNat,
        threshold_member_count=sp.TNat
    )
)

class OrganizitionFactory(sp.Contract):
    def __init__(self, params):
        sp.set_type(params, sp.TRecord(
            admin=sp.TAddress,
        ).layout(("admin")))
        sp.init(
            admin=params.admin,
            # organizations
            next_organization_id=sp.nat(1),
            organizations=sp.big_map(
                tkey=sp.TNat,
                tvalue=t_organization_record
            ),
            organization_names=sp.big_map(
                tkey=sp.TString,
                tvalue=sp.TUnit
            ),
            # record the organizition
            my_created_organizations=sp.big_map(
                tkey=sp.TNat,
                tvalue=sp.TSet(sp.TNat)
            ),

            my_joined_organizations=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TSet(sp.TNat)
            ),
            # factors
            next_factor_id=sp.nat(1),
            factors=sp.big_map(
                tkey=sp.TNat,
                tvalue=t_factor_record
            ),
        )

    @sp.entry_point
    def create_organization(self, params):
        """
        create a new organization
        """
        sp.set_type(params, t_organization_params)
        sp.verify(sp.sender == self.data.admin, "create organization required admin permission")
        sp.verify(not self.data.organization_names.contains(params.name), "Organization is exists")
        address=sp.self_address
        init_param = sp.record(
            factory=address,
            managers=params.managers,
            metadata=sp.map(
                {
                    sp.string("organization_name"): params.name,
                    sp.string("organization_logo"): params.logo,
                    sp.string("organization_decr"): params.decr,
                },
                tkey=sp.TString,
                tvalue=sp.TBytes
            )
        )
        contract = SBT.Organization(init_param) # FIXME: maybe failed
        organization_address = sp.create_contract(contract=contract)
        organization_id = self.data.next_organization_id
        # storage
        self.data.next_organization_id += 1
        self.data.organization_names[params.name] = sp.unit
        record = sp.record(
            id=organization_id,
            address=organization_address,
        )
        self.data.organizations[organization_id] = record


    @sp.entry_point
    def add_factor(self, params):
        """
        add a new factor 
        """
        sp.set_type(params, t_add_factor_params)
        sp.verify(sp.sender == self.data.admin, "add factor required admin permission")
        factor_id = self.data.next_factor_id
        factor = sp.record(
            owner=params.owner,
            address=params.address,
            pause=sp.bool(False),
            name=params.name,
            once=params.once
        )
        self.data.factors[factor_id] = factor
        self.data.next_factor_id += 1

    @sp.offchain_view()
    @sp.entry_point
    def pause_factor(self, params):
        """
        pause an factor 
        """
        sp.set_type(params, t_pause_factor_params)
        sp.verify(sp.sender == self.data.admin, "add factor required admin permission")
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

    # TODO: complete the callback functions 

    @sp.entry_point
    def on_rank_created(self, params):
        pass

    @sp.entry_point
    def on_rank_open(self, params):
        pass

    @sp.entry_point
    def on_rank_closed(self, params):
        pass

    @sp.entry_point
    def on_rank_joined(self, params):
        """
        someone join the rank
        """
        pass


sp.add_compilation_target("TezCard-Main",OrganizitionFactory(sp.record(admin=sp.address("tz1TZBoXYVy26eaBFbTXvbQXVtZc9SdNgedB"))))