

# import webapp2
# import jinja2
# import os
# import urllib

# from google.appengine.api import users
# from google.appengine.ext import ndb
# from webapp2_extras import security


######
import webapp2
import logging
import urllib
from webapp2_extras import sessions
from webapp2_extras import auth
from webapp2_extras import jinja2
from webapp2_extras import security

import models
import forms


_primaryColors={
    'Red':'#660000',
    'Black':'#000000',
    'White':'#ffffff',
    'Nave Blue':'#000033',
    'Silver':'#B0B0B0'
}

_bonusColors={
    'Lime Green':'#00FF00',
    'Purple':'#660066',
    'Yellow':'#CCFF00',
    'Orange':'#CC9900',
    'Gold':'#CCCC33'
}


#decorator
# to do: set "continue url on login redirect"
def login_required(handler):
    def check_login(self, *args, **kwargs):     
        if not self.user:
            return self.redirect_to("login")
        else:
            return handler(self, *args, **kwargs)
    return check_login   


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth(request=self.request)        

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    @webapp2.cached_property
    def user_dict(self):
        user_dict = self.auth.get_user_by_session()
        return user_dict

    @webapp2.cached_property
    def user(self):
        u = self.user_dict
        user = self.auth.store.user_model.get_by_id(u['user_id']) if u else None
        return user

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.

        # Update context 
        if self.user:
            auth_url = webapp2.uri_for("logout")
            auth_txt = 'Logout' 
        else:
            auth_url = webapp2.uri_for("login")
            auth_txt = 'Login' 

        context.update({
            'user': self.user,
            'auth_url': auth_url,
            'auth_txt': auth_txt
        })

        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)

class RegisterHandler(BaseHandler):
    def get(self):
        form = forms.RegisterForm()
        context = {'form': form}
        self.render_response('register.html', **context)

    def post(self):
        form = forms.RegisterForm(self.request.POST)
        reg_error = None
        if form.validate():
            reg_info = self.auth.store.user_model.create_user(
                "auth:" + form.username.data,
                unique_properties=['username'],
                username = form.username.data,
                email= form.email.data,
                password_raw= form.password.data
            )

            if reg_info[0]:
                self.auth.unset_session()
                self.auth.set_session(self.auth.store.user_to_dict(reg_info[1]), remember=True)
                self.redirect_to("main")
            else:
                if 'username' in reg_info[1]:
                    reg_error = 'Username is already in use'
                else:
                    reg_error = 'Something has gone terribly wrong'
      
        context = {'form': form, 'reg_error': reg_error}
        self.render_response('register.html', **context)


class LoginHandler(BaseHandler):
    def get(self):
        form = forms.LoginForm()
        context = {'form': form}
        self.render_response('login.html', **context)

    def post(self):
        form = forms.LoginForm(self.request.POST)
        auth_error = None
        if form.validate():
            try:
                self.auth.get_user_by_password("auth:"+form.username.data, form.password.data)
                self.redirect_to("main")

            except (auth.InvalidAuthIdError, auth.InvalidPasswordError), e:
                auth_error = 'Invalid username or password!'

        context = {'form': form, 'auth_error': auth_error}
        self.render_response('login.html', **context)

class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect_to('main')

class MainHandler(BaseHandler):
    def get(self):
        #Redirect to user page if signed in
        if self.user:
            self.redirect(self.uri_for('user', user_id=self.user.key.id()))
            pass
        context ={}
        self.render_response('index.html', **context)

class UserHandler(BaseHandler):
    def get(self, user_id):
        # return self.response.write(self.auth.store.user_model._properties)

        displayUser = self.auth.store.user_model.get_by_id(int(user_id))
        playersDict = {}
        if displayUser:
            for pKey in displayUser.players:
                #should be strongly consistent
                player = pKey.get()
                #this is eventualy consistent
                game = models.game.query(models.game.players == pKey).fetch(1)[0]
                numGamePlayers = len(game.players)
                gamePlayerList = [(gamePlayer, gamePlayer.get().score) for gamePlayer in game.players]
                gamePlayerList.sort(key=lambda x: x[1], reverse=True)
                rank = gamePlayerList.index((player.key, player.score)) + 1

                try:
                    pColor =  _primaryColors[player.primaryColor]
                except:
                    pColor = None
                try:
                    bColor = _bonusColors[player.bonusColor] 
                except:
                    bcolor = None

                playersDict[player.key.id()] = {
                    'game_id': game.key.id(),
                    'game_name': game.name,
                    'total_players': numGamePlayers,
                    'rank': rank,
                    'score': player.score,
                    'pColor': pColor,
                    'bColor': bColor
                }

        context = {
            'displayUser': displayUser,
            'players': playersDict
        }

        self.render_response('user.html', **context)

class NewGameHandler(BaseHandler):
    def get(self):
        form = forms.NewGameForm()
        form.color1.choices = [(key, key) for key in _primaryColors.keys()]
        form.color2.choices = [(key, key) for key in _bonusColors.keys()]

        context = {'form': form}
        self.render_response('newgame.html', **context)
    
    @login_required
    def post(self):
        form = forms.NewGameForm(self.request.POST)
        form.color1.choices = [(key, key) for key in _primaryColors.keys()]
        form.color2.choices = [(key, key) for key in _bonusColors.keys()]
        if form.validate():

            #player
            p = models.player()
            p.isAdmin = True
            p.score = 0
            p.primaryColor = form.color1.data
            p.bonusColor = form.color2.data
            p.put()
            
            #game
            g = models.game()
            g.name = form.name.data
            g.password =  security.generate_password_hash(form.password.data)
            g.primaryColorsChosen.append(form.color1.data)
            g.bonusColorsChosen.append(form.color2.data)
            g.players.append(p.key)
            g.put()

            #user
            
            self.user.players.append(p.key)
            self.user.put()

            self.redirect(self.uri_for('game', game_id=g.key.id()))

        context = {'form': form}
        self.render_response('NewGame.html', **context)

# to do: lock down join game if its full?
class GameHandler(BaseHandler):
    def get(self, game_id):

        game = models.game.get_by_id(int(game_id))
        gameMember = None
        playerDict = {}
        if game:

            for pKey in game.players:
                #should be strongly consistent
                player = pKey.get()
                #this is eventualy consistent
                user = models.User.query(models.User.players == pKey).fetch(1)[0]

                if self.user == user:
                    currentUser = True
                    gameMember = True
                else:
                    currentUser = False

                try:
                    pColor =  _primaryColors[player.primaryColor]
                except:
                    pColor = None
                try:
                    bColor = _bonusColors[player.bonusColor] 
                except:
                    bcolor = None

                playerDict[player.key.id()] = {
                    'name': user.username,
                    'score': player.score,
                    'pColor': pColor,
                    'bColor': bColor,
                    'currentUser': currentUser
                }

        context ={
            'game': game,
            'gameMember': gameMember,
            'players': playerDict
        }
        self.render_response('game.html', **context)


class AddJeepHandler(BaseHandler):
    def get(self):
        try:
            player_id = int(self.request.get("player"))
            player = models.player.get_by_id(player_id)
        except:
            player = None

        form = forms.AddJeepForm()
        if player:
            form.player.value = player.key.id()
            form.color.choices = [
                ('primaryColor', player.primaryColor),
                ('bonusColor', player.bonusColor)
            ]

        context = {
            'player': player,
            'form': form
        }
        self.render_response('addjeep.html', **context)

    @login_required
    def post(self):
        form = forms.AddJeepForm(self.request.POST)
        try:
            player_id = int(form.player.data)
            player = models.player.get_by_id(player_id)
        except:
            player = None

        auth_error = None
        if player:
            form.player.value = form.player.data
            form.color.choices = [
                ('primaryColor', player.primaryColor),
                ('bonusColor', player.bonusColor)
            ]

            # to do: validate player exists
            # to do: validate color equals primaryColor or bonusColor?
            if form.validate():
                user = self.auth.store.user_model.query(models.User.players == player.key).fetch(1)[0]
                if self.user == user:
                    
                    jeep = models.jeep(parent=player.key)
                    jeep.color = form.color.data
                    jeep.location = form.location.data
                    jeep.player = player.key
                    jeep.put()

                    if form.color.data == 'primaryColor':
                        player.score = player.score + 1
                    if form.color.data == 'bonusColor':
                        player.score = player.score + 3
                    player.put()

                    game = models.game.query(models.game.players == player.key).fetch(1)[0]
                    self.redirect(self.uri_for('game', game_id=game.key.id()))

                else:
                    auth_error = "You done goofed!"

        context = {
            'player': player,
            'form': form,
            'auth_error': auth_error
        }
        self.render_response('addjeep.html', **context)

class JoinGameHandler(BaseHandler):
    def get(self):
        try:
            game_id = int(self.request.get("game"))
            game = models.game.get_by_id(game_id)
        except:
            game = None

        form = forms.JoinGameForm()
        if game:
            form.game.value = game.key.id()
            form.color1.choices = [(key, key) for key in _primaryColors.keys() if key not in game.primaryColorsChosen]
            form.color2.choices = [(key, key) for key in _bonusColors.keys() if key not in game.bonusColorsChosen]

        context = {
            'game': game,
            'form': form
        }
        self.render_response('joingame.html', **context)


    @login_required
    def post(self):
        form = forms.JoinGameForm(self.request.POST)

        try:
            game_id = int(form.game.data)
            game = models.game.get_by_id(game_id)
        except:
            game = None

        auth_error = None
        if game:
            form.game.value = form.game.data
            form.color1.choices = [(key, key) for key in _primaryColors.keys() if key not in game.primaryColorsChosen]
            form.color2.choices = [(key, key) for key in _bonusColors.keys() if key not in game.bonusColorsChosen]

            # to do: validate game exists
            # to do: validate colors are valid (i.e., not chosen allready)
            # to do: validate password?
            # to do: validate user cannot join game twice
            if form.validate:
                if security.check_password_hash(form.password.data, game.password):
                    
                    #player
                    p = models.player()
                    p.isAdmin = False
                    p.score = 0
                    p.primaryColor = form.color1.data
                    p.bonusColor = form.color2.data
                    p.put()

                    #user
                    self.user.players.append(p.key)
                    self.user.put()

                    #game
                    game.players.append(p.key)
                    game.primaryColorsChosen.append(form.color1.data)
                    game.bonusColorsChosen.append(form.color2.data)
                    game.put()

                    self.redirect(self.uri_for('game', game_id=game.key.id()))
                else:
                    auth_error = "Invalid game password"

        context = {
            'game': game,
            'form': form, 
            'auth_error': auth_error
        }
        self.render_response('joingame.html', **context)


class FindGameHandler(BaseHandler):
    def get(self):
        game_name = self.request.get("search", None)

        try:
            offset= int(self.request.get("offset"))
            if offset < 0:
                offset = 0
        except:
            offset = 0

        if not game_name:
            qry = models.game.query()
        else:
            qry = models.game.query(models.game.name == game_name)

        count = qry.count()
        fetchSize = 10
        games = qry.fetch(fetchSize, offset=offset)

        gameDict = {}
        for game in games:

            playerCount = len(game.players)
            # admin
            # full?
            # colors chosen?

            gameDict[game.key.id()] = {
                'name': game.name,
                'count': playerCount
            }


        context = {
            'games': gameDict,
            'offset': offset,
            'fetchSize': fetchSize,
            'count': count,
            'search': urllib.quote_plus(game_name) if game_name else None

        }

        self.render_response('findgame.html', **context)





# JINJA_ENVIRONMENT = jinja2.Environment(
#     loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
#     extensions=['jinja2.ext.autoescape'],
#     autoescape=True)

# class MainHandler(webapp2.RequestHandler):
#     def get(self):


#         user = users.get_current_user()
#     	if user:
#             url = users.create_logout_url(self.request.uri)
#             url_linktext = 'Logout'
#             games = models.game.query(models.game.players.user == user)
#         else:
#             url = users.create_login_url(self.request.uri)
#             url_linktext = 'Login'
#             games = models.game.query().order(models.game.createDate).fetch(10)

#         template_values = {
#         	'games': games,
#             'user': user,
#             'url': url,
#             'url_linktext': url_linktext
#         }

#         template = JINJA_ENVIRONMENT.get_template('index.html')
#         self.response.write(template.render(template_values))

# class GameHandler(webapp2.RequestHandler):
#     def get(self, game_id):
#         game = ndb.Key('game', int(game_id)).get()

#         #validate
#         if not game:
#             self.abort(404)

#         template_values = {
#             'game': game
#         }

#         template = JINJA_ENVIRONMENT.get_template('Game.html')
#         self.response.write(template.render(template_values))


# class NewGameHandler(webapp2.RequestHandler):
#     def get(self):

#     	user = users.get_current_user()
#     	if not user:
# 			self.redirect(users.create_login_url(self.request.uri))

#         template_values = {
 
#         }

#         template = JINJA_ENVIRONMENT.get_template('NewGame.html')
#         self.response.write(template.render(template_values))


#     def post(self):
 
#         #get form data
#         user = users.get_current_user()
#         name = self.request.get('name')
#         password = self.request.get('password')
#         color = self.request.get('color')
#         bonusColor = self.request.get('bonusColor')

#         #validation
#         if not (user and name and password and color and bonusColor):
#             self.abort(403)

#         #player
#         p = player()
#         p.user = user
#         p.isAdmin = True
#         p.score = 0
#         p.color = color
#         p.bonusColor = bonusColor

#         #game
#         g = game()
#         g.name = name
#         g.password =  security.generate_password_hash(password)
#         g.players.append(p)

#         g.put()
#         self.redirect('/')

# class FindGameHandler(webapp2.RequestHandler):
#     def get(self):
#         pass

# class JoinGameHandler(webapp2.RequestHandler):
#     def get(self, game_id):
        

#         template_values = {
#             'game_id': game_id
#         }

#         template = JINJA_ENVIRONMENT.get_template('JoinGame.html')
#         self.response.write(template.render(template_values))

#     def post(self):
        
#         #get form data
#         user = users.get_current_user()
#         raw_password = self.request.get('password')
#         game_id = self.request.get('game_id')
#         color = self.request.get('color')
#         bonusColor = self.request.get('bonusColor')

#         game = ndb.Key('game', int(game_id)).get()
#         if not game:
#             self.abort(404)

#         hash_password = game.password
#         password = security.check_password_hash(raw_password, hash_password)

#         #validation
#         if not (user and password and color and bonusColor):
#             self.abort(403)

#         for p in game.players:
#             if p.user == user:
#                 self.abort(403) 

#         #player
#         p = player()
#         p.user = user
#         p.isAdmin = False
#         p.score = 0
#         p.color = color
#         p.bonusColor = bonusColor

#         game.players.append(p)
#         game.put()

#         self.redirect('/')