
from api.exceptions.notfound import NotFoundException

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException
from neo4j.exceptions import ConstraintError

class MentorDAO:

    def __init__(self, driver):
        self.driver = driver

    # tag::all[]
    def all(self):
        finalList = []
        def get_mentors(tx):
            result = tx.run("""
                MATCH (c:Mentor)
                RETURN c 
            """)
            for c in result.data():
                finalList.append(c["c"])
            return finalList

        with self.driver.session() as session:
            return session.read_transaction(get_mentors)
    # end::all[]

    # tag::allFields[]
    def all_fields(self):
        finalList = []
        def get_fields(tx):
            result = tx.run("""
                MATCH (c:Field)
                RETURN c 
            """)
            for c in result.data():
                finalList.append(c["c"])
            return finalList

        with self.driver.session() as session:
            return session.read_transaction(get_fields)
    # end::allFields[]

    # tag::createNew[]
    def createNew(self, mentorFirstName, mentorLastName, mentorEmail, mentorDescription, fields, companiesWorked):
        mentorId = mentorEmail.replace(" ", "").replace("/","").replace("(","").replace(")","")
        def add_mentor(tx, mentorId, mentorFirstName, mentorLastName, mentorEmail, mentorDescription):
            return tx.run("""
                CREATE (u:Mentor {
                    mentorId: $mentorId,
                    mentorFirstName: $mentorFirstName,
                    mentorLastName: $mentorLastName,
                    mentorEmail: $mentorEmail,
                    mentorDescription: $mentorDescription
                })
                RETURN u
            """,
            mentorId=mentorId, mentorFirstName=mentorFirstName, mentorLastName=mentorLastName, mentorEmail=mentorEmail, mentorDescription=mentorDescription).single()

        def add_field(tx, mentorId, fields):

            for x in fields:
                tx.run("""
                    MATCH (c:Mentor {
                        mentorId: $mentorId
                    })
                    MATCH (f:Field {
                        fieldId: $x['fieldId']
                    })

                    MERGE (c)-[r:INTERESTED_IN]->(f)

                """, mentorId=mentorId, x=x).single()

        def add_company(tx, mentorId, companiesWorked):

            for x in companiesWorked:
                tx.run("""
                    MATCH (m:Mentor {
                        mentorId: $mentorId
                    })
                    MATCH (c:Company {
                        companyId: $x['companyId']
                    })

                    MERGE (m)-[r:HAVE_WORKED_AT]->(c)

                """, mentorId=mentorId, companiesWorked=companiesWorked, x=x).single()

        try:
            with self.driver.session() as session:
                result = session.write_transaction(add_mentor, mentorId, mentorFirstName, mentorLastName, mentorEmail, mentorDescription)

                mentor = result['u']

                fields_result = session.write_transaction(add_field, mentor["mentorId"], fields)

                company_result = session.write_transaction(add_company, mentor["mentorId"], companiesWorked)

                payload = {
                    "mentorEmail": mentor["mentorEmail"],
                }

                return payload
        except ConstraintError as err:
            # Pass error details through to a ValidationException
            raise ValidationException(err.message, {
                "email": err.message
            })
    # end::createNew[]

    # tag::getByGenre[]
    def get_by_genre(self, name, sort='title', order='ASC', limit=6, skip=0, user_id=None):
        # Get Movies in a Genre
        def get_movies_in_genre(tx, sort, order, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
                MATCH (m:Movie)-[:IN_GENRE]->(:Genre {{name: $name}})
                WHERE exists(m.`{0}`)
                RETURN m {{
                    .*,
                    favorite: m.tmdbId in $favorites
                }} AS movie
                ORDER BY m.`{0}` {1}
                SKIP $skip
                LIMIT $limit
            """.format(sort, order)

            result = tx.run(cypher, name=name, limit=limit, skip=skip, user_id=user_id, favorites=favorites)

            return [ row.get("movie") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(get_movies_in_genre, sort, order, limit=limit, skip=skip, user_id=user_id)
    # end::getByGenre[]

    # tag::getForActor[]
    def get_for_actor(self, id, sort='title', order='ASC', limit=6, skip=0, user_id=None):
        # Get Movies for an Actor
        def get_movies_for_actor(tx, id, sort, order, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
                MATCH (:Person {{tmdbId: $id}})-[:ACTED_IN]->(m:Movie)
                WHERE exists(m.`{0}`)
                RETURN m {{
                    .*,
                    favorite: m.tmdbId in $favorites
                }} AS movie
                ORDER BY m.`{0}` {1}
                SKIP $skip
                LIMIT $limit
            """.format(sort, order)

            result = tx.run(cypher, id=id, limit=limit, skip=skip, user_id=user_id, favorites=favorites)

            return [ row.get("movie") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(get_movies_for_actor, id, sort, order, limit=limit, skip=skip, user_id=user_id)
    # end::getForActor[]

    # tag::getForDirector[]
    def get_for_director(self, id, sort='title', order='ASC', limit=6, skip=0, user_id=None):
        # Get Movies directed by a Person
        def get_movies_for_director(tx, id, sort, order, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
                MATCH (:Person {{tmdbId: $id}})-[:DIRECTED]->(m:Movie)
                WHERE exists(m.`{0}`)
                RETURN m {{
                    .*,
                    favorite: m.tmdbId in $favorites
                }} AS movie
                ORDER BY m.`{0}` {1}
                SKIP $skip
                LIMIT $limit
            """.format(sort, order)

            result = tx.run(cypher, id=id, limit=limit, skip=skip, user_id=user_id, favorites=favorites)

            return [ row.get("movie") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(get_movies_for_director, id, sort, order, limit=limit, skip=skip, user_id=user_id)
    # end::getForDirector[]

    # tag::findById[]
    def find_by_id(self, user_id, mentorId):

        def find_mentor_by_id(tx, user_id, mentorId):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
            MATCH (m:Mentor {mentorId: $mentorId})
            RETURN m {
                .*,
                favorite: m.mentorId IN $favorites
            } AS mentor
            """
            result = tx.run(cypher, user_id=user_id, mentorId=mentorId, favorites=favorites).single()

            if result == None:
                raise NotFoundException()

            return result.get("mentor")

        with self.driver.session() as session:
            return session.read_transaction(find_mentor_by_id, user_id, mentorId)
    # end::findById[]

    # tag::getSimilarMentors[]
    def get_similar_mentors(self, id, limit=6, skip=0, user_id=None):
        # Get similar mentors
        def find_similar_mentors(tx, id, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)
            
            cypher = """
            MATCH (:Mentor {mentorId: $id})-[:BELONGS_TO|HAS_FAVORITE_MENTOR]->()<-[:BELONGS_TO|HAS_FAVORITE_MENTOR]-(m)

            WITH m, count(*) AS inCommon
            WITH m, inCommon, m.imdbRating * inCommon AS score
            ORDER BY score DESC

            SKIP $skip
            LIMIT $limit

            RETURN m {
                .*,
                score: score,
                favorite: m.mentorId IN $favorites
            } AS mentor
            """

            result = tx.run(cypher, id=id, limit=limit, skip=skip, favorites=favorites)

            return [ row.get("mentor") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(find_similar_mentors, id, limit, skip, user_id)
    # end::getSimilarMovies[]

    # tag::getUserFavorites[]
    def get_user_favorites(self, tx, user_id):

        if user_id == None:
            return []
        result = tx.run("""
            MATCH (u:User {userId: $userId})-[:HAS_FAVORITE_MENTOR]->(m)
            RETURN m.mentorId AS id
        """, userId=user_id)

        return [ record.get("id") for record in result ]
    # end::getUserFavorites[]