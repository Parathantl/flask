from api.exceptions.notfound import NotFoundException

class FavoriteDAO:

    def __init__(self, driver):
        self.driver=driver

    # tag::all[]
    def all_course(self, user_id, sort = 'title', order = 'ASC', limit = 6, skip = 0):

        with self.driver.session() as session:
            courses = session.read_transaction(lambda tx: tx.run("""
                MATCH (u:User {{userId: $userId}})-[r:HAS_FAVORITE]->(m:Course)
                RETURN m {{
                    .*,
                    favorite: true
                }} AS course
                ORDER BY m.`{0}` {1}
                SKIP $skip
                LIMIT $limit
            """.format(sort, order), userId=user_id, limit=limit, skip=skip).value("course"))

            return courses
    # end::all[]

    # tag::add-course[]
    def add_course(self, userId, courseId):

        def add_course_to_favorites(tx, userId, courseId):
            ratings = self.get_user_rated(tx, userId, courseId)

            row = tx.run("""
                MATCH (u:User {userId: $userId})
                MATCH (c:Course {courseId: $courseId})

                MERGE (u)-[r:HAS_FAVORITE]->(c)
                SET r.favorite = true

                RETURN c {
                    .*,
                    favorite: true,
                    rating: $ratings[0]
                } AS course
            """, userId=userId, courseId=courseId, ratings=ratings).single()

            if row == None:
                raise NotFoundException()

            return row.get("course")

        with self.driver.session() as session:
            return session.write_transaction(add_course_to_favorites, userId, courseId)
        
    # end::add_course[]

    # tag::remove_course[]
    def remove_course(self, user_id, courseId):
        def remove_from_favorites(tx, user_id, courseId):
            ratings = self.get_user_rated(tx, user_id, courseId)

            row = tx.run("""
                MATCH (u:User {userId: $userId})-[r:HAS_FAVORITE]->(m:Course {courseId: $courseId})
                DELETE r

                RETURN m {
                    .*,
                    favorite: false,
                    rating: $ratings[0]
                } AS course
            """, userId=user_id, courseId=courseId, ratings=ratings).single()

            if row == None:
                raise NotFoundException()

            return row.get("course")

        with self.driver.session() as session:
            return session.write_transaction(remove_from_favorites, user_id, courseId)
    # end::remove_course[]

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