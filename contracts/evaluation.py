import smartpy as sp
import operator
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")

# 1. 创建 SBT 合约。和 TokenID
# 2. factor_list setting （address_list weight_list ） （single / batch）
# 3. set_rank_pattern(sbt_address, token_id, type, threhold)
# 4. open_rank(sbt_address, token_id), close_rank(sbt_address, token_id)

class EvaluationPolicy:

    def __init__(self):
        self.data.sbt_factor_map = sp.big_map({}, tkey = sp.TAddress,
            tvalue = sp.Record(address_list = sp.list,
                                weight_list = sp.list,
                                type = sp.TNat,
                                threshold = sp.TNat,
                                member_factor_value_map = sp.big_map({}, tkey = sp.TAddress
                                                                        tvalue = sp.list(sp.pair(factor_address = sp.TAddress, factor_value = sp.TNat))
                                                                    )
                               )
                            )
        self.data.sbt_pass_address_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.set)


    @sp.entry_point
    def set_factor_list(self, dao_sbt_contract, address_list, weight_list):
        # verify address and weight
        self.verify(len(sp.address_list) == len(sp.weight_list), "address and weight not equal")
        aRecord = sp.record(field1 = address_list, field2 = weight_list)
        self.data.sbt_factor_map[dao_sbt_contract] = aRecord

    @sp.entry_point
    def set_rank_pattern(self, sbt_address, type, threshold):
        sbt_factor_record = self.data.sbt_factor_map[sbt_address]
        sbt_factor_record.type = type
        sbt_factor_record.threshold = threshold

    @sp.entry_point
    def factor_report(self, member_address, sbt_address, value):
        aRecord = sp.data.sbt_factor_map[sbt_address]
        aRecord.member_factor_value_map[member_address] = sp.pair(factor_address = self.sender, factor_value = value)

    @sp.entry_point
    def open_rank(self, sbt_address):
        # verify sbt_factor_map contain sbt_address
        self.verify(self.data.sbt_factor_map.contains(sbt_address), "sbt factor have not set")
        # verify sbt_factor_map contain sbt_address
        self.verify(self.data.rank_map.contains(sbt_address), "sbt factor have not set")

        sbt_factor_record = self.data.sbt_factor_map[sbt_address]
        address_weight_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TNat)

        len = sp.len(sbt_factor_record.address_list)
        sp.for i in sp.range(1, len, step = 1):
            address_weight_map[sbt_factor_record.address_list[i] = sbt_factor_record.weight_list[i]

        # storage factor sum everyone
        sbt_address_value_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TNat)

        sp.for address in sbt_factor_record.member_factor_value_map.keys():
            factor_pair_list = sbt_factor_record.member_factor_value_map[address]
            sum = 0
            sp.for y_pair in factor_pair_list:
                factor_address = sp.fst(y_pair)
                sum += (address_weight_map[factor_address] * sp.snd(y_pair))
            sbt_address_value_map[address] = sum

        # check type=1 fetch rank top threshold , type = 2 fetch > threshold
        sp.if sbt_factor_record.type == 1:
            # todo
            sorted(sbt_address_value_map.items(), key = operator.itemgetter(1), reverse = True)
            address_list = sbt_address_value_map.keys()
            sp.for i in sp.range(1, sbt_factor_record.threshold, step = 1):
                self.data.sbt_pass_address_map[k].add(address_list[i])

        sp.if sbt_factor_record.type == 2:
            sp.for k in sbt_address_value_map.keys():
                sp.if sbt_address_value_map[k] > sbt_factor_record.threshold:
                    self.data.sbt_pass_address_map[k].add(k)




