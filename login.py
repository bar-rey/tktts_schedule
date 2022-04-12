from flask_login import UserMixin

class User(UserMixin):
	def create(self, user):
		self.__user = user
		return self
	
	def get_id(self):
		return str(self.__user['id'])

	@property
	def role(self):
		return self.__user['role']

	@property
	def vk_id(self):
		return self.__user['vk_id']