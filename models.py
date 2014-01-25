from webapp2_extras.appengine.auth.models import User
from google.appengine.ext import ndb

class User(User):
	username = ndb.StringProperty()
	email = ndb.StringProperty()
	players = ndb.KeyProperty(kind='player', repeated=True)

class jeep(ndb.Model):
	color = ndb.StringProperty()
	location = ndb.StringProperty()
	createDate = ndb.DateTimeProperty(auto_now_add=True)
	player = ndb.KeyProperty(kind='player')

class game(ndb.Model):
	players = ndb.KeyProperty(kind='player', repeated=True)
	name = ndb.StringProperty()
	password = ndb.StringProperty()
	createDate = ndb.DateTimeProperty(auto_now_add=True)
	primaryColorsChosen = ndb.StringProperty(repeated=True)
	bonusColorsChosen = ndb.StringProperty(repeated=True)

class player(ndb.Model):
	isAdmin = ndb.BooleanProperty()
	score = ndb.IntegerProperty()
	primaryColor = ndb.StringProperty()
	bonusColor = ndb.StringProperty()
	createDate = ndb.DateTimeProperty(auto_now_add=True)