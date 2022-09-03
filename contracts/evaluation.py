import smartpy as sp
import operator
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

# 1. create SBT contract and TokenID
# 2. factor_list setting （address_list weight_list ） （single / batch）
# 3. set_rank_pattern(sbt_address, token_id, type, threhold)
# 4. open_rank(sbt_address, token_id), close_rank(sbt_address, token_id)

class Evaluation(sp.Contract):

    def __init__(self, administrator, global_id):
        # evaluation storage
        self.init(
                    administrator = administrator, # administrator
                    global_id = global_id, # global id
                    dao_rank_id_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TList(sp.TNat)), # <dao, list<rank_id>>
                    # map: key=rank_id, value=rank_params
                    sbt_factor_map = sp.big_map({}, tkey = sp.TNat,
                                            tvalue = sp.Record(
                                                        status = sp.TNat, # rank_id status 1=open 0 = close
                                                        join_users = sp.set(sp.TAddress), # join user set
                                                        factor_weight_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TNat),
                                                        type = sp.TNat,
                                                        threshold = sp.TNat,
                                                        member_factor_value_map = sp.big_map({}, tkey = sp.TAddress
                                                                                               tvalue = sp.TList(
                                                                                                    sp.pair(factor_address = sp.TAddress,
                                                                                                            factor_value = sp.TNat))
                                                                                   )
                                                      )
                                      ),
                    sbt_pass_address_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.set)
        )

    @sp.entry_point
    def receive_factor(self, params):
        sp.set_type(params, sp.Record(
            dao = sp.TAddress, # dao address
            rank_id = sp.TNat, # rank id
            address = sp.TAddress, # user_address
            weight = sp.TNat # factor weight
        ))
        factor_address = self.sender
        # business logic
        # check factor_address is valid in dao
        self.verify(self.data.sbt_factor_map[params.rank_id].factors.contains(factor_address))
        # storage
        self.data.sbt_factor_map[params.rank_id].member_factor_value_map[params.address].push(sp.pair(factor_address, params.weight))

        # (dao, rank_id, user, factor) -> unique
        # calculate total score
        factor_pair_list = self.data.sbt_factor_map[params.rank_id].member_factor_value_map[params.address]
        sum = 0
        sp.for y_pair in factor_pair_list:
            factor = sp.fst(y_pair)
            sum += (self.data.sbt_factor_map[params.rank_id].address_weight_map[factor] * sp.snd(y_pair))
        self.if sum > self.data.sbt_factor_map[params.rank_id].threshold:
            # storage
            self.data.sbt_pass_address_map[params.dao].add(params.address)


    @sp.entry_point
    def create_rank(self, params):
		sp.set_type(params, sp.TRecord(
			dao = sp.TAddress,
			factors = sp.TList(sp.TAddress),
			weights = sp.TList(sp.TNat)
		))
        self.verify(self.sender == self.data.administrator)
        self.verify(sp.len(self.params.factors) == sp.len(self.params.weights))

        factor_weight_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TNat)
        len = sp.len(self.data.sbt_factor_map[params.rank_id].factors)
        sp.for i in sp.range(1, len, step = 1):
            factor_weight_map[params.factors[i]] = params.weights[i]

		# generate rank_id
        new_rank_id = self.data.global_id + 1
        self.data.global_id = new_rank_id
        self.data.sbt_factor_map[new_rank_id] = sp.TRecord(
            status = 1,
            factor_weight_map = factor_weight_map
        )
        # storage dao of rank_id
        self.data.dao_rank_id_map[params.dao].push(new_rank_id)

		# callback


    @sp.entry_point
    def open_rank(self, params):
        sp.set_type(params, sp.TRecord(
                                rank_id = sp.TNat,
                                type = sp.TNat,
                                threshold = sp.TNat
                            )
        )
        self.verify(self.sender == self.data.administrator)
        self.verify(self.data.sbt_factor_map.contains(params.rank_id))

        self.data.sbt_factor_map[params.rank_id].type = params.type
        self.data.sbt_factor_map[params.rank_id].threshold = params.threshold


    @sp.entry_point
    def join_rank(self, params):
        sp.set_type(params, sp.TRecord(
            dao = sp.TAddress,
            rank_id = sp.TNat
        ))
        # check dao and rank_id exist
        self.verify(self.data.dao_rank_id_map.contains(params.dao))
        self.verify(self.data.dao_rank_id_map[dao].contains(params.rank_id))
        # check rank is open or not
        self.verify(self.data.sbt_factor_map[params.rank_id].status == 1)
        # storage
        self.verify(! self.data.sbt_factor_map[params.rank_id].join_users.contains(self.sender))

        self.data.sbt_factor_map[params.rank_id].join_users.add(self.sender)

        ## callback