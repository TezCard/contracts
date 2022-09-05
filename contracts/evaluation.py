from multiprocessing import managers
from re import A
from signal import pause
from contracts.sbt import Organization
import smartpy as sp

SBT = sp.io.import_script_from_url("file://sbt.py")
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

# 1. create SBT contract and TokenID
# 2. factor_list setting （address_list weight_list ） （single / batch）
# 3. set_rank_pattern(sbt_address, token_id, type, threhold)
# 4. open_rank(sbt_address, token_id), close_rank(sbt_address, token_id)

t_organization_params = sp.TRecord(
    managers=sp.TList(sp.TAddress),
    name=sp.TString,
    logo=sp.TString,
    symbol=sp.TString,
).layout(("managers", ("name", ("logo", "symbol"))))

t_organization_record = sp.TRecord(
    id=sp.TNat,
    address=sp.TAddress,
    name=sp.TString,
    logo=sp.TString,
    symbol=sp.TString,
    managers=sp.TList(sp.TAddress),
).layout(("id", ("address", ("name", ("logo", ("symbol", "managers"))))))

t_add_factor_params = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TString,
    address=sp.TAddress
).layout(("owner", ("name", "address")))

t_factor_record = sp.TRecord(
    owner=sp.TAddress,
    name=sp.TString,
    address=sp.TAddress,
    pause=sp.TBool
).layout(("owner", ("name", ("address", "pause"))))

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

t_create_rank_params = sp.TRecord(
    organization_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weights=sp.TList(sp.TNat),
    variable=t_rank_variables
).layout("organization_id", ("factors", ("weights", "variable")))

t_rank_record = sp.TRecord(
    organization_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weight=sp.TList(sp.TNat),
    open=sp.TBool,
    variable=t_rank_variables,
    pause=sp.TBool,
).layout(("organization_id", ("factors", ("weight", ("open", ("pause", "variable"))))))

t_open_rank_params = sp.TRecord(
    id=sp.TNat
).layout(("id"))

t_join_rank_params = sp.TRecord(
    organization_id=sp.TNat,
    rank_id=sp.TNat
).layout(("organization_id", "rank_id"))

t_on_join_rank_callback_params = sp.TRecord(
    user=sp.TAddress,
    rank_id=sp.TNat
).layout("user", "rank_id")

t_is_member_params = sp.TRecord(
    user=sp.TAddress,

)


class TezCardFactory(sp.Contract):
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
            # ranks
            next_rank_id=sp.nat(1),
            ranks=sp.big_map(
                tkey=sp.TNat,
                tvalue=t_rank_record
            )
        )

    @sp.entry_point
    def create_organization(self, params):
        """
        create a new organization
        """
        sp.set_type(params, t_organization_params)
        sp.verify(sp.sender == self.data.admin, "create organization required admin permission")
        sp.verify(not self.data.organization_names.contains(params.name), "Organization is exists")
        # TODO:george create a new Organization contract
        # TODO:george add new logic for query my organization
        organization_id = self.data.next_organization_id
        # storage
        self.data.next_organization_id += 1
        self.data.organization_names[params.name] = sp.none
        sp.set_set_result_type(sp.TNat)
        sp.result(organization_id)

    @sp.entry_point
    def on_mint_callback(self, params):
        """
        callback from the underlying SBT
        TODO:george  complete it to verify if user mint the SBT now
        """
        pass

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
            # TODO: maybe need once ?
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
    def list_factor(self, params):
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

    @sp.entry_point
    def create_rank(self, params):
        sp.set_type(params, t_create_rank_params)
        rank_id = self.data.next_rank_id
        sp.verify(self.data.organizations.contains(params.organization_id), "organization is not exists")
        organization = self.data.organizations[params.organization_id]
        # FIXME: remove the admin check to the SBT inner callback
        sp.verify(organization.managers.contains(sp.sender), "operator is not manager of this organization")
        rank = sp.record(
            #             organization_id=params.organization_id,
            rank_id=rank_id,
            factors=params.factors,
            weights=params.weights,
            open=sp.bool(False),
            variable=params.variable,
            pause=sp.bool(False)
        )
        # callback to the organization
        on_create_rank = sp.Contract(t_rank_record, organization.address, "on_create_rank").open_some(
            "address is not TezCard DAO")
        sp.transfer(rank, sp.tez(0), on_create_rank)
        # FIXME: not save move the record into the SBT inner 
        self.data.next_rank_id += 1

    @sp.entry_point
    def open_rank(self, params):
        # TODO: I think move this entry into the SBT is soundness
        sp.set_type(params, t_open_rank_params)
        sp.verify(self.data.organizations.contains(params.organization_id), "organization is not exists")
        organization = self.data.organizations[params.organization_id]
        # only managers can open rank
        sp.verify(organization.managers.contains(sp.sender), "operator is not manager of this organization")
        # callback to the organization contract SBT
        on_open_rank = sp.Contract(sp.TUnit, organization.address, "on_open_rank").open_some(
            "address is not the TezCard SBT")
        sp.transfer(sp.unit, sp.tez(0), on_open_rank)

    @sp.entry_point
    def join_rank(self, params):
        sp.set_type(params, t_join_rank_params)
        # check organization is valid
        sp.verify(self.data.organizations.contains(params.organization_id), "organization is not exists")
        # check rank is valid
        sp.verify(self.data.ranks.contains(params.rank_id), "rank is not exists")
        # check organization and rank is match
        sp.verify(self.data.ranks[params.rank_id].organization_id == params.organization_id,
                  "organization and rank is not match")
        # check rank in still work
        sp.verify(self.data.ranks[params.rank_id].open == sp.sp.bool(True), "rank have already closed")
        # TODO:george how to make user to know if the rank is still work ?

        ## callback to a single function
        # fixed-rank
        # time-elapsed
        organization = self.data.organizations[params.organization_id]
        on_join_rank = sp.Contract(t_on_join_rank_callback_params, organization.address, "on_join_rank").open_some(
            "address is not the TezCard SBT")
        sp.transfer(sp.record(user=sp.sender, rank_id=params.rank_id), sp.tez(0), "on_join_rank")

        # storage
        self.data.my_joined_organizations[sp.sender].add(params.organization_id)

    # offchain views
    @sp.offchain_view()
    @sp.onchain_view()
    def if_memebr(self, params):
        # on-chain view let the voting contract to know if a member is a memebr 
        pass

    @sp.offchain_view()
    @sp.onchain_view()
    def is_admin(self, params):
        # on-chain view let the voting contract to create a new voting for this dao
        pass

    @sp.offchain_view()
    @sp.onchain_view()
    def get_rank(self, params):
        pass

    @sp.offchain_view()
    def list_rank(self, params):
        # global TezCard Rank Dashboard for all users 
        pass

    @sp.offchain_view()
    def query_organization(self, param):
        sp.set_type(param, sp.TString)
        sp.set_result_type(sp.TBool)
        with sp.if self.data.organization_names.contains(param):
            sp.result(sp.bool(True))
        with sp.else:
            sp.result(sp.bool(False))


@sp.offchain_view()
def list_my_joined_orgnazition(self, param):
    sp.set_type(param, sp.TAddress)
    organization_ids = self.data.my_joined_organizations[param]
    res = sp.TList(t_organization_record)
    with sp.for x in organization_ids:
        res.push(self.dao.organizations[x])
    sp.set_result_type(sp.TList(t_organization_record))
    sp.result(res)
