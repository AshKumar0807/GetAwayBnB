from flask import Flask, render_template,url_for, redirect
app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main_page.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

if __name__ == '__main__':
    app.run()