from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity, jwt_required
from api.dao.mentors import MentorDAO
from api.dao.ratings import RatingDAO

mentor_routes = Blueprint("mentors", __name__, url_prefix="/api/mentors")

@mentor_routes.route('/', methods=['POST'])
def create():
    form_data = request.get_json()['results']

    mentorFirstName = form_data['mentorFirstName']
    mentorLastName = form_data['mentorLastName']
    mentorEmail = form_data['mentorEmail']
    mentorDescription = form_data['mentorDescription']
    fields = form_data['fields']
    companiesWorked = form_data['companiesWorked']

    dao = MentorDAO(current_app.driver)

    mentor = dao.createNew(mentorFirstName, mentorLastName, mentorEmail, mentorDescription, fields, companiesWorked)

    return mentor

@mentor_routes.route('/', methods=['GET'])
def get_mentors():
    # sort = request.args.get("sort", "title")
    # order = request.args.get("order", "ASC")
    # limit = request.args.get("limit", 6, type=int)
    # skip = request.args.get("skip", 0, type=int)

    user_id = current_identity["sub"] if current_identity != None else None

    dao = MentorDAO(current_app.driver)

    output = dao.all()

    return jsonify(output)

@mentor_routes.route('/fields', methods=['GET'])
def get_fields_detail():
    # sort = request.args.get("sort", "title")
    # order = request.args.get("order", "ASC")
    # limit = request.args.get("limit", 6, type=int)
    # skip = request.args.get("skip", 0, type=int)

    dao = MentorDAO(current_app.driver)

    output = dao.all_fields()

    return jsonify(output)
    
@mentor_routes.route('/<mentor_id>', methods=['GET'])
@jwt_required()
def get_mentor_details(mentor_id):

    user_id = current_identity["sub"] if current_identity != None else None

    dao = MentorDAO(current_app.driver)

    mentor = dao.find_by_id(user_id, mentor_id)

    return jsonify(mentor)

@mentor_routes.route('/<mentor_id>/ratings', methods=['GET'])
def get_mentor_ratings(mentor_id):
    sort = request.args.get("sort", "timestamp")
    order = request.args.get("order", "ASC")
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    dao = RatingDAO(current_app.driver)

    ratings = dao.for_mentor(mentor_id, sort, order, limit, skip)

    return jsonify(ratings)

@mentor_routes.route('/<mentor_id>/similar', methods=['GET'])
@jwt_required()
def get_similar_mentors(mentor_id):
    user_id = current_identity["sub"] if current_identity != None else None

    dao = MentorDAO(current_app.driver)

    output = dao.get_similar_mentors(mentor_id, user_id)

    return jsonify(output)
