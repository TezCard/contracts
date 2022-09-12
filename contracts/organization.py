"""
TezCard SBT contract
In TezCard world every thing maybe a SBT

TODO: rename to Organization and mixin the logic of rank operation
close rank
"""
import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

#########
# Types #
#########

t_rank_variables = sp.TVariant(
    fixed_rank=sp.TRecord(
        threshold_score_limit=sp.TNat,
        threshold_member_limit=sp.TOption(sp.TNat)
    ).layout(("threshold_score_limit", "threshold_member_limit")),
    time_elapsed=sp.TRecord(
        threshold_block_level=sp.TNat,
        threshold_member_limit=sp.TNat
    ).layout(("threshold_block_level", "threshold_member_limit"))
)

t_create_rank_params = sp.TRecord(
    organization_id=sp.TNat,
    name=sp.TBytes,
    decr=sp.TBytes,
    factors=sp.TMap(sp.TNat, sp.TNat),
    variable=t_rank_variables
).layout(("organization_id", ("name", ("decr", ("factors", "variable")))))

t_rank_score_record = sp.TRecord(
    candidates=sp.TMap(sp.TAddress, sp.TNat),
    max_score=sp.TNat,
    min_score=sp.TNat
).layout(("candidates", ("max_score", "min_score")))

t_rank_record = sp.TRecord(
    rank_id=sp.TNat,
    next_record_id=sp.TNat,
    name=sp.TBytes,
    decr=sp.TBytes,
    factors=sp.TMap(sp.TNat, sp.TNat),
    open=sp.TBool,
    variable=t_rank_variables,
    waiting=sp.TBool,
    scores=t_rank_score_record
).layout((
    "rank_id",
    (
        "next_record_id",
        (
            "name",
            (
                "decr",
                (
                    "factors",
                    (
                        "open",
                        (
                            "variable",
                            (
                                "waiting",
                                "scores"
                            )
                        )
                    )
                )
            )
        )
    )
))


t_rank_join_params = sp.TRecord(
    rank_id=sp.TNat
).layout(("rank_id"))

t_rank_join_record = sp.TRecord(
    participant=sp.TAddress,
    rank_id=sp.TNat,
    score=sp.TNat,
)

t_rank_open_params = sp.TRecord(
    rank_id=sp.TNat,
).layout(("rank_id"))

t_rank_close_params = sp.TRecord(
    rank_id=sp.TNat,
).layout(("rank_id"))

t_init_organization_param = sp.TRecord(
    factory=sp.TAddress,
    managers=sp.TMap(sp.TAddress, sp.TUnit),
    metadata=sp.TMap(sp.TString, sp.TBytes)
)

t_receive_score_callback_params = sp.TRecord(
    participant=sp.TAddress,
    rank_id=sp.TNat,
    factor_id=sp.TNat,
    score=sp.TNat
).layout(("participant", ("rank_id", ("factor_id", "score"))))

t_list_rank_params = sp.TVariant(
    waiting=sp.TRecord(
        limit=sp.TNat,
        offset=sp.TNat
    ).layout(("limit", "offset")),
    opening=sp.TRecord(
        limit=sp.TNat,
        offset=sp.TNat
    ).layout(("limit", "offset")),
    closed=sp.TRecord(
        limit=sp.TNat,
        offset=sp.TNat
    ).layout(("limit", "offset"))
)

t_list_my_join_rank_params = sp.TRecord(
    limit=sp.TNat,
    offset=sp.TNat
).layout(("limit", "offset"))

class Organization(FA2.Fa2Nft,
                   FA2.OffchainviewTokenMetadata,
                   FA2.OnchainviewBalanceOf):
    """
    TezCard Organization abstraction, in the TezCard the Organization is the core
    concept live in every tool in the toolbox.
    """

    def __init__(self, params):
        sp.set_type(params, t_init_organization_param)
        FA2.Fa2Nft.__init__(self, params.metadata, policy=FA2.NoTransfer())
        self.update_initial_storage(
            # id distribution
            next_rank_id=sp.nat(0),
            # ranks list
            ranks=sp.big_map({}, tkey=sp.TNat, tvalue=t_rank_record),
            # rank records 
            join_records=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TBigMap(sp.TAddress, t_rank_join_record)),
            # managers of this Organization
            managers=params.managers, 
            # OrganizationFactory contract address used to callback
            factory=params.factory,
            # the bottle used to contain the Organization member soul
            bottle=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TNat),
            # my joined rank
            my_joined_rank=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TList(sp.TNat)),
            # open rank
            opened_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            # close rank
            closed_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            # waiting for open
            waiting_ranks=sp.big_map({}, tkey=sp.TNat, tvalue=sp.TUnit),
            # whitelist
            white_list=sp.big_map({}, tkey=sp.TAddress, tvalue=sp.TUnit)
        )
    
    @sp.entry_point
    def create_rank(self, params):
        """
        create a new rank in this organization  
        """
        sp.set_type(params, t_create_rank_params)
        sp.verify(self.data.managers.contains(sp.sender), "create rank must have the manager permission")
        rank_id = self.data.next_rank_id + 1
        record = sp.record(
            rank_id=rank_id,
            next_record_id=sp.nat(0),
            name=params.name,
            decr=params.decr,
            factors=params.factors,
            open=sp.bool(True),
            variable=params.variable,
            waiting=sp.bool(True),
            scores=sp.record(
                candidates=sp.map({}, tkey=sp.TAddress, tvalue=sp.TNat),
                max_score=sp.nat(0),
                min_score=sp.nat(0)
            )
        )
        self.data.ranks[rank_id] = record
        self.data.join_records[rank_id] = sp.big_map({}, tkey=sp.TAddress, tvalue=t_rank_join_record)
        self.data.waiting_ranks[rank_id]=sp.unit
        self.data.next_rank_id += 1
        # TODO: callback to the Factory to indexing 

    @sp.entry_point
    def open_rank(self, params):
        """
        open a rank
        move from waiting list to the open list
        """
        sp.set_type(params, t_rank_open_params)
        sp.verify(self.data.managers.contains(sp.source), "open rank must have admin permission")
        rank = self.data.ranks[params.rank_id]
        sp.verify(rank.open, "rank must be open")
        sp.verify(rank.waiting, "rank must be waiting now")
        rank.open = sp.bool(True)
        rank.waiting=sp.bool(False)

        # try remove from the waiting list
        with sp.if_(self.data.waiting_ranks.contains(params.rank_id)):
            del self.data.waiting_ranks[params.rank_id]
 
        self.data.opened_ranks[params.rank_id]=sp.unit
        # TODO: callback to the Factory the Rank is Open
    

    @sp.entry_point
    def close_rank(self, params):
        """
        close a rank 
        move from open list to close list
        """
        sp.set_type(params, t_rank_close_params)
        sp.verify(self.data.managers.contains(sp.source), "open rank must have admin permission")
        self._close_rank(params.rank_id)
        #TODO: callback to the Factory the Rank is Close

    def _close_rank(self, rank_id):
        """
        close action for the rank 
        """
        sp.set_type(rank_id, sp.TNat)
        rank = self.data.ranks[rank_id]
        sp.verify(rank.open, "rank must be open now")
        rank.open = sp.bool(False) 
        # modify the indexing storage
        with sp.if_(self.data.opened_ranks.contains(rank_id)):
            del self.data.opened_ranks[rank_id]
        self.data.closed_ranks[rank_id]=sp.unit
        #

    @sp.entry_point
    def join_rank(self, params):
        """
        some user want to join this rank everyone only have one soulbound token in this Org 
        """
        sp.set_type(params, t_rank_join_params)
        sp.verify(self.data.bottle.contains(sp.source), "user have already joined this organization")
        sp.verify(self.data.ranks.contains(params.rank_id), "rank not found")
        address = sp.source
        rank = self.self.data.ranks[params.rank_id]
        sp.verify(rank.open, "rank must be still open")
        record_id = rank.next_record_id + 1
        sp.verify(self.data.join_records.contains(record_id), "rank records not found")
        join_record=self.data.join_records[record_id]
        record = sp.record(
            participant=address,
            rank_id=params.rank_id,
            score=sp.nat(0)
        )
        join_record[address] = record
        with sp.if_(self.data.my_joined_rank.contains(address)):
            self.data.my_joined_rank[address].push(params.rank_id)
        with sp.else_():
            self.data.my_joined_rank[address] = sp.list([params.rank_id])
        # TODO: callback to the Factory to indexing
 
    @sp.entry_point
    def mint(self):
        # last_token_id from the NFT 
        # adapt from FA2 
        with sp.if_(self.data.white_list.contains(sp.source)):
            token_id = sp.compute(self.data.last_token_id)
            metadata = sp.record(token_id=token_id, token_info=sp.map(l={}, tkey=sp.TString, tvalue=sp.TBytes))
            self.data.token_metadata[token_id] = metadata
            self.data.ledger[token_id] = self.source
            self.data.last_token_id += 1 
            del self.data.white_list[sp.source]
            # TODO: callback to the Factory to indexing 
        with sp.else_():
            sp.failwith("user not in the white list")


    @sp.entry_point
    def receive_score(self, params):
        sp.set_type(params, t_receive_score_callback_params)
        sp.verify(sp.sender == self.data.factory, "only let the factory contract to call")
        #TODO: handle the dispatcher 
        pass

    def calculate_score_fixed_rank(self, params, member_limit):
        sp.set_type(params, t_receive_score_callback_params)
        sp.set_type(member_limit, sp.TOption(sp.TNat))

        sp.verify(self.data.ranks.contains(params.rank_id), "rank must exists in this organization")
        rank = self.data.ranks[params.rank_id]
        join_records = self.data.join_records[params.rank_id]
        sp.verify(not rank.waiting and rank.open, "rank must open and still work now")

        factors = rank.factors
        sp.verify(factors.contains(params.factor_id), "factor is not exists in this rank")

        weight = factors[params.factor_id]
        score = weight * params.score
        join_records[params.participant].score = score

        # update the rank
        total = join_records[params.participant].score
        scores = rank.scores
        # if member limit is some then update the list and try close
        with sp.if_(member_limit.is_some()):
            limit = member_limit.open_some()
            with sp.if_(sp.len(scores.candidates) < limit):
                variable = rank.variable
                parameter = variable.open_variant("fixed_rank")
                limit = parameter.threshold_score_limit
                with sp.if_(total >= limit):
                    scores.candidates[params.participant] = total
                    # issue the white list
                    self.white_list[params.participand] = sp.unit
                    # update max min
                    with sp.if_(total < scores.min_score):
                        scores.min_score = total
                    with sp.if_(total > scores.max_score):
                        scores.max_score = total
                    with sp.if_(sp.len(scores.candidates) == limit):
                        self._close_rank(params.rank_id)
        with sp.else_():
            # just put in to the scores
            variable = rank.variable
            parameter = variable.open_variant("fixed_rank")
            limit = parameter.threshold_score_limit
            with sp.if_(total >= limit):
                scores.candidates[params.participant] = total
                # issue the white list
                self.white_list[params.participand] = sp.unit
                # update max min
                with sp.if_(total < scores.min_score):
                    scores.min_score = total
                with sp.if_(total > scores.max_score):
                    scores.max_score = total
        rank.scores = scores

    def calculate_score_time_elapsed(self, params, member_limit):
        sp.set_type(params, t_receive_score_callback_params)
        sp.set_type(member_limit, sp.TNat)

        sp.verify(self.data.ranks.contains(params.rank_id), "rank must exists in this organization")
        current_block = sp.level
        rank = self.data.ranks[params.rank_id]
        sp.verify(not rank.waiting and rank.open, "rank must open and still work now")

        join_records = self.data.join_records[params.rank_id]
        variable = rank.variable.open_variant("time_elapsed")

        
        with sp.if_(current_block < variable.threshold_block_level):
            # TODO: should check on-chain sort to care about the safety 
            pass
        with sp.else_():
            self._close_rank(params.rank_id)

    # TODO: add manager CURD methods

    @sp.onchain_view()
    def is_rank_open(self):
        """
        used for the factor contract to read to decide if should report score
        """
        sp.set_type(rank_id, sp.TNat)
        rank = self.data.ranks[rank_id]
        sp.verify(rank.open, "rank must be open now")
        sp.result(sp.bool(rank.open))

    @sp.offchain_view()
    def list_ranks(self, params):
        sp.set_type(params, t_list_rank_params)
        # TODO: use the page logic to hanlde this

    @sp.offchain_view()
    def get_rank_details(self, rank_id):
        sp.set_type(rank_id, sp.TNat)
        rank = self.data.ranks[rank_id]
        sp.result(rank)

    @sp.offchain_view()
    def is_in_bottle(self):
        """
        return if the user is in the bottle has minted the Token
        """
        sp.result(sp.bool(False))

@sp.add_test(name="Minimal")
def test():
    scenario = sp.test_scenario()
    metadata = {
        "name": "Contract Name",
        "description": "A description about the contract",
        "version": 1,
    }
    c1 = Organization(factory="1213", managers={"123": "vd", "2323": "vd"}, metadata={"123": metadata})
    scenario += c1
    """ Test views """
    # Display the offchain call result
    scenario.show(c1.is_in_bottle(1))