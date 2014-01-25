import os
import sys

# Third party libraries path must be fixed before importing webapp2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import webapp2
from webapp2_extras.routes import RedirectRoute
import handlers

#debug
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

#config
config = {
    # webapp2 sessions
    'webapp2_extras.sessions': {'secret_key': '_PUT_KEY_HERE_YOUR_SECRET_KEY_'},

    # webapp2 authentication
    'webapp2_extras.auth': {'user_model': 'models.User'}
}

#routes
routes = [
    RedirectRoute('/', handlers.MainHandler, name='main', strict_slash=True),
    RedirectRoute('/register', handlers.RegisterHandler, name='register', strict_slash=True),
    RedirectRoute('/login', handlers.LoginHandler, name='login', strict_slash=True),
    RedirectRoute('/logout', handlers.LogoutHandler, name='logout', strict_slash=True),
    RedirectRoute('/user/<user_id>', handlers.UserHandler, name='user', strict_slash=True),
    RedirectRoute('/game/<game_id>', handlers.GameHandler, name='game', strict_slash=True),
    RedirectRoute('/newgame', handlers.NewGameHandler, name='newgame', strict_slash=True),
    RedirectRoute('/addjeep', handlers.AddJeepHandler, name='addjeep', strict_slash=True),
    RedirectRoute('/joingame', handlers.JoinGameHandler, name='findgame', strict_slash=True),
    RedirectRoute('/findgame', handlers.FindGameHandler, name='joingame', strict_slash=True)
]
# app = webapp2.WSGIApplication([
#     ('/', MainHandler),
#     ('/newgame', NewGameHandler),
#     ('/findgame', FindGameHandler),
#     ('/joingame', JoinGameHandler),
#     ('/joingame/(\d+)', JoinGameHandler),
#     ('/game/(\d+)', GameHandler)
# ], debug=True)


app = webapp2.WSGIApplication(debug=debug, config=config, routes=routes)

#add custom errors

