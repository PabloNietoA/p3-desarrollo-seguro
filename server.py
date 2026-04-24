from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.permanent_session_lifetime = 99999999

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

