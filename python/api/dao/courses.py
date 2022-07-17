from api.exceptions.notfound import NotFoundException

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException
from neo4j.exceptions import ConstraintError

class CourseDAO:

    def __init__(self, driver):
        self.driver = driver

    # tag::all[]
    def all(self):
        finalList = []
        def get_courses(tx):
            result = tx.run("""
                MATCH (c:Course)
                RETURN c 
            """)
            for c in result.data():
                finalList.append(c["c"])
            return finalList

        with self.driver.session() as session:
            return session.read_transaction(get_courses)
    # end::all[]

    # tag::createNew[]
    def createNew(self, courseName, courseLink, courseDescription, fields):
        courseId = courseName.replace(" ", "").replace("/","").replace("(","").replace(")","")
        def add_course(tx, courseId, courseName, courseLink, courseDescription):
            return tx.run("""
                CREATE (u:Course {
                    courseId: $courseId,
                    courseName: $courseName,
                    courseLink: $courseLink,
                    courseDescription: $courseDescription
                })
                RETURN u
            """,
            courseId=courseId, courseName=courseName, courseLink=courseLink, courseDescription=courseDescription).single()

        def add_field(tx, courseId, fields):

            for x in fields:
                tx.run("""
                    MATCH (c:Course {
                        courseId: $courseId
                    })
                    MATCH (f:Field {
                        fieldId: $x['fieldId']
                    })

                    MERGE (c)-[r:BELONGS_TO]->(f)

                """, courseId=courseId, x=x).single()

        try:
            with self.driver.session() as session:
                result = session.write_transaction(add_course, courseId, courseName, courseLink, courseDescription)

                course = result['u']

                fields_result = session.write_transaction(add_field, course["courseId"], fields)

                payload = {
                    "courseName": course["courseName"],
                }

                return payload
        except ConstraintError as err:
            # Pass error details through to a ValidationException
            raise ValidationException(err.message, {
                "email": err.message
            })
    # end::createNew[]

    # tag::findById[]
    def find_by_id(self, user_id, courseId):

        def find_course_by_id(tx, user_id, courseId):
            favorites = self.get_user_favorites(tx, user_id)
            ratings = self.get_user_rated(tx, user_id, courseId)

            cypher = """
            MATCH (m:Course {courseId: $courseId})
            RETURN m {
                .*,
                favorite: m.courseId IN $favorites,
                rating: $ratings[0]
            } AS course
            """
            result = tx.run(cypher, user_id=user_id, courseId=courseId, favorites=favorites, ratings=ratings).single()

            if result == None:
                raise NotFoundException()

            return result.get("course")

        with self.driver.session() as session:
            return session.read_transaction(find_course_by_id, user_id, courseId)
    # end::findById[]

    # tag::getSimilarCourses[]
    def get_similar_courses(self, id, limit=6, skip=0, user_id=None):
        # Get similar courses
        def find_similar_courses(tx, id, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
            MATCH (:Course {courseId: $id})-[:BELONGS_TO|HAS_FAVORITE]->()<-[:BELONGS_TO|HAS_FAVORITE]-(m)

            WITH m, count(*) AS inCommon
            WITH m, inCommon, m.imdbRating * inCommon AS score
            ORDER BY score DESC

            SKIP $skip
            LIMIT $limit

            RETURN m {
                .*,
                score: score,
                favorite: m.courseId IN $favorites
            } AS course
            """

            result = tx.run(cypher, id=id, limit=limit, skip=skip, favorites=favorites)

            return [ row.get("course") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(find_similar_courses, id, limit, skip, user_id)
    # end::getSimilarMovies[]

    # tag::getUserFavorites[]
    def get_user_favorites(self, tx, user_id):

        if user_id == None:
            return []
        result = tx.run("""
            MATCH (u:User {userId: $userId})-[:HAS_FAVORITE]->(m)
            RETURN m.courseId AS id
        """, userId=user_id)

        return [ record.get("id") for record in result ]
    # end::getUserFavorites[]

    # tag::getUserRated[]
    def get_user_rated(self, tx, user_id, course_id):

        if user_id == None:
            return []
        result = tx.run("""
            MATCH (u:User {userId: $userId})-[r:RATED]->(m:Course {courseId: $courseId})
            RETURN r.rating AS rating
        """, userId=user_id, courseId=course_id)

        return [ record.get("rating") for record in result ]
    # end::getUserFavorites[]