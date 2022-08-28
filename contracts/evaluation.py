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
                                threhold = sp.TNat,
                                member_factor_value_map = sp.big_map({}, tkey = sp.TAddress
                                                                        tvalue = sp.list(sp.pair(factor_address = sp.TAddress, factor_value = sp.TNat))
                                                                    )
                               )
                            )
        self.data.rank_threhold_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.TNat)
        self.data.sbt_pass_address_map = sp.big_map({}, tkey = sp.TAddress, tvalue = sp.set)


    @sp.entry_point
    def set_factor_list(self, dao_sbt_contract, address_list, weight_list):
        # verfiy address and weight
        self.verify(len(sp.address_list) == len(sp.weight_list), "address and weight not equal")
        aRecord = sp.record(field1 = address_list, field2 = weight_list)
        self.data.sbt_factor_map[dao_sbt_contract] = aRecord

    @sp.entry_point
    def set_rank_pattern(self, sbt_address, type, threhold):
        sbt_factor_record = self.data.sbt_factor_map[sbt_address]
        sbt_factor_record.type = type
        sbt_factor_record.threhold = threhold

    @sp.entry_point
    def open_rank(self, sbt_address):
        # verify sbt_factor_map contain sbt_address
        self.verify(self.data.sbt_factor_map.contains(sbt_address), "sbt factor have not set")
        # verify sbt_factor_map contain sbt_address
        self.verify(self.data.rank_map.contains(sbt_address), "sbt factor have not set")

        sbt_factor_record = self.data.sbt_factor_map[sbt_address]
        sbt_factor_record.member_factor_value_map


        sp.for x in sbt_factor_record.address_list:
            aRecord = self.data.factor_value_map[sbt_address]


    @sp.entry_point
    def factor_report(self, member_address, sbt_address, value):
        aRecord = sp.data.sbt_factor_map[sbt_address]
        aRecord.member_factor_value_map[member_address] = sp.pair(factor_address = self.sender, factor_value = value)

