from api.exceptions.notfound import NotFoundException

class RatingDAO:

    def __init__(self, driver):
        self.driver=driver

    # tag::add[]
    def addCourseRating(self, user_id, course_id, rating):
        # Create function to save the rating in the database
        def create_course_rating(tx, user_id, course_id, rating):
            favorites = self.get_user_favorites(tx, user_id)
            ratings = self.get_user_rated(tx, user_id, course_id)

            return tx.run("""
            MATCH (u:User {userId: $user_id})
            MATCH (c:Course {courseId: $course_id})

            MERGE (u)-[r:RATED]->(c)
            SET r.rating = $rating,
                r.timestamp = timestamp()

            RETURN c {
                .*,
                favorite: c.courseId IN $favorites,
                rating: r.rating
            } AS course
            """, user_id=user_id, course_id=course_id, rating=rating, favorites=favorites, ratings=ratings).single()

        with self.driver.session() as session:
            record = session.write_transaction(create_course_rating, user_id=user_id, course_id=course_id, rating=rating)

            if record is None:
                raise NotFoundException()

            return record["course"]
    # end::add[]

    # tag::removeRating[]
    def removeCourseRating(self, user_id, course_id):

        def remove_course_rating(tx, user_id, course_id):
            
            favorites = self.get_user_favorites(tx, user_id)
            ratings = self.get_user_rated(tx, user_id, course_id)

            return tx.run("""

            MATCH (u:User {userId: $user_id})-[r:RATED]->(c:Course {courseId: $course_id})
            DELETE r

            RETURN c {
                .*,
                favorite: c.courseId IN $favorites
            } AS course
            """, user_id=user_id, course_id=course_id, favorites=favorites, ratings=ratings).single()

        with self.driver.session() as session:
            record = session.write_transaction(remove_course_rating, user_id=user_id, course_id=course_id)

            if record is None:
                raise NotFoundException()

            return record["course"]
    # end::removeRating[]

    # tag::add[]
    def addMentorRating(self, user_id, mentorId, rating):
        # Create function to save the rating in the database
        def create_mentor_rating(tx, user_id, mentorId, rating):
            favorites = self.get_user_favorites_mentor(tx, user_id)
            ratings = self.get_user_rated_mentor(tx, user_id, mentorId)

            return tx.run("""
            MATCH (u:User {userId: $user_id})
            MATCH (c:Mentor {mentorId: $mentorId})

            MERGE (u)-[r:RATED]->(c)
            SET r.rating = $rating,
                r.timestamp = timestamp()

            RETURN c {
                .*,
                favorite: c.mentorId IN $favorites,
                rating: r.rating
            } AS course
            """, user_id=user_id, mentorId=mentorId, rating=rating, favorites=favorites, ratings=ratings).single()

        with self.driver.session() as session:
            record = session.write_transaction(create_mentor_rating, user_id=user_id, mentorId=mentorId, rating=rating)

            if record is None:
                raise NotFoundException()

            return record["course"]
    # end::add[]

    # tag::removeRating[]
    def removeMentorRating(self, user_id, mentorId):

        def remove_mentor_rating(tx, user_id, mentorId):
            print("comes here....")
            favorites = self.get_user_favorites_mentor(tx, user_id)
            ratings = self.get_user_rated_mentor(tx, user_id, mentorId)

            return tx.run("""

            MATCH (u:User {userId: $user_id})-[r:RATED]->(c:Mentor {mentorId: $mentorId})
            DELETE r

            RETURN c {
                .*,
                favorite: c.mentorId IN $favorites
            } AS course
            """, user_id=user_id, mentorId=mentorId, favorites=favorites, ratings=ratings).single()

        with self.driver.session() as session:
            record = session.write_transaction(remove_mentor_rating, user_id=user_id, mentorId=mentorId)

            if record is None:
                raise NotFoundException()

            return record["course"]
    # end::removeRating[]

    # tag::forCourse[]
    def for_course(self, courseId, sort = 'timestamp', order = 'ASC', limit = 6, skip = 0):
        # Get ratings for a Course
        def get_course_ratings(tx, courseId, sort, order, limit):
            cypher = """
            MATCH (u:User)-[r:RATED]->(m:Course {{courseId: $courseId}})
            RETURN r {{
                .rating,
                .timestamp,
                user: u {{
                    .userId, .name
                }}
            }} AS review
            ORDER BY r.`{0}` {1}
            SKIP $skip
            LIMIT $limit
            """.format(sort, order)

            result = tx.run(cypher, courseId=courseId, limit=limit, skip=skip)

            return [ row.get("review") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(get_course_ratings, courseId, sort, order, limit)
    # end::forCourse[]

    # tag::forMentors[]
    def for_mentor(self, mentorId, sort = 'timestamp', order = 'ASC', limit = 6, skip = 0):
        # Get ratings for a Course
        def get_mentor_ratings(tx, mentorId, sort, order, limit):
            cypher = """
            MATCH (u:User)-[r:RATED]->(m:Course {{courseId: $courseId}})
            RETURN r {{
                .rating,
                .timestamp,
                user: u {{
                    .userId, .name
                }}
            }} AS review
            ORDER BY r.`{0}` {1}
            SKIP $skip
            LIMIT $limit
            """.format(sort, order)

            result = tx.run(cypher, mentorId=mentorId, limit=limit, skip=skip)

            return [ row.get("review") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(get_mentor_ratings, mentorId, sort, order, limit)
    # end::forCourse[]

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

    # tag::getUserFavoritesMentor[]
    def get_user_favorites_mentor(self, tx, user_id):

        if user_id == None:
            return []
        result = tx.run("""
            MATCH (u:User {userId: $userId})-[:HAS_FAVORITE_MENTOR]->(m)
            RETURN m.mentorId AS id
        """, userId=user_id)

        return [ record.get("id") for record in result ]
    # end::getUserFavorites[]

    # tag::getUserRatedMentor[]
    def get_user_rated_mentor(self, tx, user_id, mentorId):

        if user_id == None:
            return []
        result = tx.run("""
            MATCH (u:User {userId: $userId})-[r:RATED]->(m:Mentor {mentorId: $mentorId})
            RETURN r.rating AS rating
        """, userId=user_id, mentorId=mentorId)

        return [ record.get("rating") for record in result ]
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