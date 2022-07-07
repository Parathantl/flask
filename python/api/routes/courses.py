from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity, jwt_required
from api.dao.ratings import RatingDAO
from api.dao.courses import CourseDAO
import json

course_routes = Blueprint("courses", __name__, url_prefix="/api/courses")

@course_routes.route('/', methods=['POST'])
def create():
    form_data = request.get_json()['results']

    courseName = form_data['courseName']
    courseLink = form_data['courseLink']
    courseDescription = form_data['courseDescription']
    fields = form_data['fields']

    dao = CourseDAO(current_app.driver)

    course = dao.createNew(courseName, courseLink, courseDescription, fields)
    return course

@course_routes.route('/', methods=['GET'])
def get_courses():
    # sort = request.args.get("sort", "title")
    # order = request.args.get("order", "ASC")
    # limit = request.args.get("limit", 6, type=int)
    # skip = request.args.get("skip", 0, type=int)

    user_id = current_identity["sub"] if current_identity != None else None

    dao = CourseDAO(current_app.driver)

    output = dao.all()

    return jsonify(output)
    
@course_routes.route('/<course_id>', methods=['GET'])
@jwt_required()
def get_course_details(course_id):

    user_id = current_identity["sub"] if current_identity != None else None

    dao = CourseDAO(current_app.driver)

    course = dao.find_by_id(user_id, course_id)

    return jsonify(course)

@course_routes.route('/<course_id>/ratings', methods=['GET'])
def get_course_ratings(course_id):
    sort = request.args.get("sort", "timestamp")
    order = request.args.get("order", "ASC")
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    dao = RatingDAO(current_app.driver)

    ratings = dao.for_course(course_id, sort, order, limit, skip)

    return jsonify(ratings)

@course_routes.route('/<course_id>/similar', methods=['GET'])
@jwt_required()
def get_similar_courses(course_id):
    user_id = current_identity["sub"] if current_identity != None else None

    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    dao = CourseDAO(current_app.driver)

    output = dao.get_similar_courses(course_id, limit, skip, user_id)

    return jsonify(output)
