from flask import *
from flask.ext.login import LoginManager, login_required, current_user
import os
from database import *
#CONFIG

SECRET_KEY = 'super_secret'
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']



#SETUP
app = Flask(__name__)
app.config.from_object(__name__)




login_manager = LoginManager()
login_manager.init_app(app)


#DATABASE STUFF
@login_manager.user_loader
def load_user(userid):
	return User.query.get(userid)



#VIEWS

@app.route('/')
def index():
	subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
	return render_template("subforums.html", subforums=subforums)

@app.route('/subforum')
def subforum():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
	subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
	path = generateLinkPath(subforum_id)
	return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=path)

@app.route('/loginform')
def loginform():
	return render_template("login.html")


@login_required
@app.route('/addpost')
def addpost():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()

	return render_template("createpost.html", subforum=subforum)

@app.route('/viewpost')
def viewpost():
	postid = int(request.args.get("post"))
	post = Post.query.filter(Post.id == postid).first()
	return render_template("viewpost.html", post=post)

#ACTIONS

@login_required
@app.route('/action_post', methods=['POST', 'GET'])
def action_post():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return redirect(url_for("subforums"))

	user = current_user
	title = request.form['title']
	content = request.form['content']
	#check for valid posting
	errors = []
	retry = False
	if not valid_title(title):
		errors.append("Title must be between 4 and 140 characters long!")
		retry = True
	if not valid_content(content):
		errors.append("Post must be between 10 and 5000 characters long!")
		retry = True
	if retry:
		return render_template("createpost.html",subforum=subforum,  errors=errors)
	post = Post(title, content)
	subforum.posts.append(post)
	user.posts.append(post)
	db.session.commit()
	return redirect("/subforum?sub=" + str(subforum_id))


@app.route('/action_login', methods=['POST'])
def action_login():
	username = request.form['username']
	password = request.form['password']
	user = User.query.filter(User.username == username).first()
	if user and user.check_password(password):
		login_user(user)
	else:
		errors = []
		errors.append("Username or password is incorrect!")
		return render_template("login.html", errors=errors)
	return redirect(url_for("index"))


@login_required
@app.route('/action_logout')
def action_logout():
	#todo
	logout_user()
	return redirect(url_for("index"))

@app.route('/action_createaccount', methods=['POST'])
def action_createaccount():
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']
	errors = []
	retry = False
	if username_taken(username):
		errors.append("Username is already taken!")
		retry=True
	if email_taken(email):
		errors.append("An account already exists with this email!")
		retry = True
	if not valid_username(username):
		errors.append("Username is not valid!")
		retry = True
	if not valid_password(password):
		errors.append("Password is not valid!")
		retry = True
	if retry:
		return render_template("login.html", errors=errors)
	user = User(email, username, password)
	db.session.add(user)
	db.session.commit()
	login_user(user)
	return redirect(url_for("index"))

#MANAGEMENT
def add_subforum(title, description, parent=None):
	sub = Subforum(title, description)
	if parent:
		parent.subforums.append(sub)
	else:
		db.session.add(sub)

	db.session.commit()
	return sub
def init_site():
	admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here")
	add_subforum("Announcements", "View forum announcements here",admin)
	add_subforum("Bug Reports", "Report bugs with the forum here", admin)
	add_subforum("General Discussion", "Use this subforum to post anything you want")
	add_subforum("Other", "Discuss other things here")
	user = User("kyl@spe.com", "admin", "password")
	db.session.add(user)
	db.session.commit()

def generateLinkPath(subforumid):
	links = []
	subforum = Subforum.query.filter(Subforum.id == subforumid).first()
	parent = Subforum.query.filter(Subforum.id == subforum.parent_id).first()
	links.append("<a href=\"/subforum?sub=" + str(subforum.id) + "\">" + subforum.title + "</a>")
	while parent is not None:
		links.append("<a href=\"/subforum?sub=" + str(parent.id) + "\">" + parent.title + "</a>")
		parent = Subforum.query.filter(Subforum.id == parent.parent_id).first()
	links.append("<a href=\"/\">Forum Index</a>")
	link = ""
	for l in reversed(links):
		link = link + " / " + l
	return link
#DATABASE STUFF

if __name__ == "__main__":
	db.create_all()
	if not User.query.all():
		init_site()
	port = int(os.environ.get("PORT", 33507))
	app.run(host='0.0.0.0', port=port, debug=True)

	
