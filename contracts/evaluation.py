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


t_orgnazition_params = sp.TRecord(
    managers=sp.TList(sp.TAddress),
    name=sp.TString,
    logo=sp.TString,
    symbol=sp.TString,
).layout(("managers",("name", ("logo", "symbol"))))

t_orgnazition_record = sp.TRecord(
    id=sp.TNat,
    address=sp.TAddress,
    managers=sp.TMap( # FIXME: maybe we should move it into the SBT inner 
        tkey=sp.TAddress,
        tvalue=sp.TUnit
    )
).layout(("id", ("address", "managers")))

t_add_factor_params = sp.TRecord(
    owner=sp.TAddress,
    addresss=sp.TAddress,
    name=sp.TString
).layout(("owner", ("name", "address")))

t_factor_record = sp.TRecord(
    owner=sp.TAddress,
    address=sp.TAddress,
    pause=sp.TBool,
    name=sp.TString
).layout(("owner", ("address", ("pause", "name"))))

t_pause_factor_params = sp.TRecord(
    factor_id=sp.TNat,
    pause=sp.TBool
).layout(("factor_id", "pause"))

t_list_factor_params = sp.TRecord(
    offset=sp.TNat,
    limit=sp.TNat
).layout(("offset", "limit"))


t_rank_variables = sp.TVariant(
    fixed_rank = sp.TRecord(
        threhold_score=sp.TNat
    ),
    time_elapsed = sp.TRecord(
        threhold_block_level=sp.TNat,
        threhold_member_count = sp.TNat
    )
)

t_create_rank_params = sp.TRecord(
    orgnazition_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weight=sp.TList(sp.TNat),
    variable=t_rank_variables
).layout("orgnazition_id", ("factors", ("weight", "variable")))

t_rank_record = sp.TRecord(
    orgnazition_id=sp.TNat,
    factors=sp.TList(sp.TNat),
    weight=sp.TList(sp.TNat),
    open=sp.TBool,
    variable=t_rank_variables,
    pause=sp.TBool,
).layout(("orgnazition_id", ("factors", ("weight", ("open", ("pause","variable"))))))

t_open_rank_params = sp.TRecord(
    id=sp.TNat
).layout(("id"))

t_join_rank_params = sp.TRecord(
    orgnazition_id=sp.TNat,
    rank_id=sp.TNat
).layout(("orgnazition_id", "rank_id"))

t_on_join_rank_callback_params = sp.TRecord(
    user=sp.TAddress,
    rank_id=sp.TNat
).layout("user", "rank_id")

t_is_member_params=sp.TRecord(
    user=sp.TAddress,

)

class TezCardFactory(sp.Contract):
    def __init__(self, params):
        sp.set_type(params, sp.TRecord(
            admin=sp.TAddress,
        ).layout(("admin")))
        sp.init(
            admin=sp.TAddress,
            # orgnazitions
            next_orgnazition_id=sp.TNat,
            orgnazitions=sp.big_map(
                tkey=sp.TAddress,
                tvalue=t_orgnazition_record
            ),
            orgnazition_names=sp.big_map(
                tkey=sp.TString,
                tvalue=sp.TUnit
            ),
            my_created_orgnazitions=sp.big_map(
                tkey=sp.TNat,
                tvalue=sp.TUnit
            ),
            my_joined_orgnazitions=sp.big_map(
                tkey=sp.TNat,
                tvalue=sp.TUnit
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
    def create_orgnazition(self, params):
        """
        create a new orgnazition  
        """
        sp.set_type(params, t_orgnazition_params)
        sp.verify(not self.data.names.contains(params.name), "Orgnazition is exists")
        # TODO:george create a new Orgnazition contract
        # TODO:george add new logic for query my orgnazition 
    
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

    @sp.entry_point
    def pause_factor(self, params):
        """
        pause an factor 
        """
        sp.set_type(params, t_pause_factor_params)
        sp.verify(sp.sender == self.data.admin, "add factor required admin permission")
        self.data.factors[params.factor_id].pause=sp.bool(params.pause)

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
        rank_id=self.data.next_rank_id
        sp.verify(self.data.orgnazitions.contains(params.orgnazition_id), "orgnazition is not exists")
        orgnazition = self.data.orgnazitions[params.orgnazition_id]
        # FIXME: remove the admin check to the SBT inner callback
        sp.verify(orgnazition.managers.contains(sp.sender), "operator is not manager of this orgnazition")
        rank = sp.record(
            orgnazition_id=params.orgnazition_id,
            factors=params.factors,
            weight=params.weight,
            open=sp.bool(False),
            variable=params.variable,
            pause=sp.bool(False)
        )
        # callback to the orgnazition 
        on_create_rank = sp.Contract(t_rank_record, orgnazition.address, "on_create_rank").open_some("address is not TezCard DAO")
        sp.transfer(rank, sp.tez(0), on_create_rank)
        # FIXME: not save move the record into the SBT inner 
        self.data.next_rank_id += 1

    @sp.entry_point
    def open_rank(self, params):
        # TODO: I think move this entry into the SBT is soundness 
        sp.set_type(params, t_open_rank_params)        
        sp.verify(self.data.orgnazitions.contains(params.orgnazition_id), "orgnazition is not exists")
        orgnazition = self.data.orgnazitions[params.orgnazition_id]
        # callback to the orgnazition contract SBT
        on_open_rank = sp.Contract(sp.TUnit, orgnazition.address, "on_open_rank").open_some("address is not the TezCard SBT")
        sp.transfer(sp.unit, sp.tez(0), on_open_rank)
        
    @sp.entry_point
    def join_rank(self, params):
        sp.set_type(params, t_join_rank_params)
        sp.verify(self.data.orgnazitions.contains(params.orgnazition_id), "orgnazition is not exists")
        # TODO:george how to make user to know if the rank is still work ?
        ## callbackto a single function 
        # fixed-rank 
        # time-elapsed 
        orgnazition = self.data.orgnazitions[params.orgnazition_id]
        on_join_rank = sp.Contract(t_on_join_rank_callback_params, orgnazition.address, "on_join_rank").open_some("address is not the TezCard SBT")
        sp.transfer(sp.record(user=sp.source, rank_id=params.rank_id), sp.tez(0), "on_join_rank")


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
    def list_my_orgnazition(self, params):
        pass

    @sp.offchain_view()
    def list_my_joined_orgnazition(self, params):
        pass