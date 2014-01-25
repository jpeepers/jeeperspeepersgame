from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, HiddenField, RadioField, validators

class NewGameForm(Form):
	name = StringField('Game Name', [validators.Required(), validators.Length(min=1, max=35)])
	password = PasswordField('Game Password', [validators.Required(), validators.Length(min=8, max=35)])
	color1 = SelectField('Primary Color', [validators.Required()])
	color2 = SelectField('Bonus Color', [validators.Required()])

class JoinGameForm(Form):
	game = HiddenField('game', [validators.Required()])
	password = PasswordField('Game Password', [validators.Required(), validators.Length(min=8, max=35)])
	color1 = SelectField('Primary Color', [validators.Required()])
	color2 = SelectField('Bonus Color', [validators.Required()])

class RegisterForm(Form):
	username = StringField('Username', [validators.Required(), validators.Length(min=1, max=35)])
	email = StringField('Email', [validators.Required(), validators.Email()])
	password = PasswordField('Password', [validators.Required(), validators.EqualTo('password_confirm', message="Passwords must match."), validators.Length(min=8, max=35)])
	password_confirm = PasswordField('Confirm Password', [validators.Required(), validators.Length(min=8, max=35)])

class LoginForm(Form):
	username = StringField('Username', [validators.Required()])
	password = PasswordField('Password', [validators.Required()])

class AddJeepForm(Form):
	player = HiddenField('Player', [validators.Required()])
	color = RadioField('Jeep Color', [validators.Required()])
	location = StringField('Location', [validators.Required(), validators.Length(max=35)])