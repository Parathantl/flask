from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity
import json

from api.dao.people import PeopleDAO

people_routes = Blueprint("people", __name__, url_prefix="/api/people")

@people_routes.route('/', methods=['GET'])
def get_index():
    # Get Pagination Values
    q = request.args.get("q")
    sort = request.args.get("sort", "title")
    order = request.args.get("order", "ASC")
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    # Create an instance of the PeopleDAO
    dao = PeopleDAO(current_app.driver)

    # Get output
    output = dao.all(q, sort, order, limit, skip)

    jsonObj = json.dumps(output, default=str)
    return jsonObj

@people_routes.get('/<id>')
def get_person(id):
    # Create an instance of the PeopleDAO
    dao = PeopleDAO(current_app.driver)

    # Get the person
    person = dao.find_by_id(id)

    jsonObj = json.dumps(person, indent=1, sort_keys=True, default=str)
    return json.loads(jsonObj), 200


@people_routes.get('/<id>/similar')
def get_similar_people(id):
    # Get Pagination Values
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    # Create an instance of the PeopleDAO
    dao = PeopleDAO(current_app.driver)

    # Get the person
    similar = dao.get_similar_people(id, limit, skip)

    jsonObj = json.dumps(similar, indent=1, sort_keys=True, default=str)
    return jsonObj
