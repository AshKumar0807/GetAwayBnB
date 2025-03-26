from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from models import db, Property

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

with app.app_context():
        db.create_all()

#login_manager = LoginManager()
#login_manager.init_app(app) uncomment this when actual user date is added

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/upload_property', methods=['GET', 'POST'])

def upload_property():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        price = request.form['price']
        maxGuests = request.form['maxGuests']

        new_property = Property(
            hostID=1, #current_user.userID,
            title=title,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            price=price,
            maxGuests=maxGuests
        )
        
        db.session.add(new_property)
        db.session.commit()
        
        flash("Property uploaded successfully!", "success")
        return redirect(url_for('upload_property'))

    return render_template('upload_property.html')

if __name__ == '__main__':
    app.run(debug=True)
