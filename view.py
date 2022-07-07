from flask import Flask, render_template
import os

from datetime import timedelta
import os

from flask import Flask
from flask.helpers import send_from_directory
from flask_cors import CORS

from flask_jwt import JWT

from api.exceptions.notfound import NotFoundException

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException

from api.neo4j import init_driver

from api.routes.auth import auth_routes
from api.routes.account import account_routes
from api.routes.movies import movie_routes
from api.routes.genres import genre_routes
from api.routes.people import people_routes
from api.routes.status import status_routes

from api.routes.courses import course_routes
from api.routes.mentors import mentor_routes
from api.routes.companies import company_routes
from api.routes.query import query_routes

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config.from_mapping(
    NEO4J_URI=os.getenv('NEO4J_URI'),
    NEO4J_USERNAME=os.getenv('NEO4J_USERNAME'),
    NEO4J_PASSWORD=os.getenv('NEO4J_PASSWORD'),
    NEO4J_DATABASE=os.getenv('NEO4J_DATABASE'),
    SECRET_KEY=os.getenv('JWT_SECRET'),
    JWT_AUTH_HEADER_PREFIX="Bearer",
    JWT_VERIFY_CLAIMS="signature",
    JWT_EXPIRATION_DELTA=timedelta(360)
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

with app.app_context():
    init_driver(
        app.config.get('NEO4J_URI'),
        app.config.get('NEO4J_USERNAME'),
        app.config.get('NEO4J_PASSWORD'),
    )

    # JWT
def authenticate(username, password):
    pass

def identify(payload):
    payload["userId"] = payload["sub"]
    return payload

jwt = JWT(app, authenticate, identify)

# Register Routes
app.register_blueprint(auth_routes)
app.register_blueprint(account_routes)
app.register_blueprint(genre_routes)
app.register_blueprint(movie_routes)
app.register_blueprint(people_routes)
app.register_blueprint(status_routes)

app.register_blueprint(course_routes)
app.register_blueprint(company_routes)
app.register_blueprint(mentor_routes)
app.register_blueprint(query_routes)

@app.route('/')
def home():
    return {"hello": "world"}


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3001))
    app.run(debug=True, host='0.0.0.0', port=port)
