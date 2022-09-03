import smartpy as sp

class FactorFactory(sp.Contract):

	def __init__(self, administrator):
		self.init(
		    # administrator may be wallet address or voting address
		    administrator = administrator,
		    factor_list = sp.TList(sp.TRecord(
		                                owner = sp.TAddress,
		                                factor_address = sp.TAddress
		                            )
		                   )
		)


	def add_factor(self, params):
		sp.set_type(params, sp.TRecord(
                                owner = sp.TAddress,
                                factor_address = sp.TAddress
		                    )
		)
		sp.verify(self.sender == self.data.administrator)
		# storage factor
		self.data.factor_list.push(params)

	def remove_factor(self, params):
		sp.set_type(params, sp.TRecord(
                                        owner = sp.TAddress,
                                        factor_address = sp.TAddress
        		                    )
        )
        sp.verify(self.sender == self.data.administrator)
        # remove factor
        self.data.factor_list.remove(params)

	def list_factor(self, params):
		sp.set_type(params, sp.TRecord(
			offset = sp.TNat,
			limit = sp.TNat
		))