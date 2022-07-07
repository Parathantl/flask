from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity
from api.dao.ratings import RatingDAO
from api.dao.companies import CompanyDAO
import json

company_routes = Blueprint("companies", __name__, url_prefix="/api/companies")

@company_routes.route('/', methods=['POST'])
def create():
    form_data = request.get_json()['results']

    companyName = form_data['companyName']
    companyAddress = form_data['companyAddress']
    companyEmail = form_data['companyEmail']
    companyWeb = form_data['companyWeb']

    dao = CompanyDAO(current_app.driver)

    company = dao.createNew(companyName, companyAddress, companyEmail, companyWeb)

    return company

@company_routes.get('/')
def get_companies():
    # sort = request.args.get("sort", "title")
    # order = request.args.get("order", "ASC")
    # limit = request.args.get("limit", 6, type=int)
    # skip = request.args.get("skip", 0, type=int)

    dao = CompanyDAO(current_app.driver)

    output = dao.all()

    return jsonify(output)

@company_routes.get('/<course_id>')
def get_course_details(course_id):

    dao = CompanyDAO(current_app.driver)

    course = dao.find_by_id(course_id)

    jsonObj = json.dumps(course, indent=1, sort_keys=True, default=str)
    return json.loads(jsonObj), 200

@company_routes.get('/<course_id>/ratings')
def get_course_ratings(course_id):
    sort = request.args.get("sort", "timestamp")
    order = request.args.get("order", "ASC")
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    dao = RatingDAO(current_app.driver)

    ratings = dao.for_course(course_id, sort, order, limit, skip)

    return jsonify(ratings)

@company_routes.get('/<course_id>/similar')
def get_similar_courses(course_id):
    user_id = current_identity["sub"] if current_identity != None else None

    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    dao = CompanyDAO(current_app.driver)

    output = dao.get_similar_courses(course_id, limit, skip, user_id)

    return jsonify(output)
