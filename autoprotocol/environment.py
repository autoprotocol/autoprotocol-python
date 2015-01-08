

class Environment(object):

	def __init__(self, 
					protocol = None, 
					samples = [], 
					params = {},
					container_pool = [],
					resourcedb = None):

		# The Transcriptic protocol object to which to append commands
		self.protocol = protocol
		self.samples = samples
		self.params = params
		self.container_pool = container_pool
		self.resourcedb = resourcedb

