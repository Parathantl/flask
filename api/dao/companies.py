
from api.exceptions.notfound import NotFoundException

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException
from neo4j.exceptions import ConstraintError

class CompanyDAO:

    def __init__(self, driver):
        self.driver = driver

    # tag::all[]
    def all(self):
        finalList = []
        def get_companies(tx):
            result = tx.run("""
                MATCH (c:Company)
                RETURN c 
            """)
            for c in result.data():
                finalList.append(c["c"])
            return finalList

        with self.driver.session() as session:
            return session.read_transaction(get_companies)
    # end::all[]

    # tag::createNew[]
    def createNew(self, companyName, companyAddress, companyEmail, companyWeb):
        companyId = companyName.replace(" ", "").replace("/","")
        def add_company(tx, companyId, companyName, companyAddress, companyEmail, companyWeb):
            return tx.run("""
                CREATE (u:Company {
                    companyId: $companyId,
                    companyName: $companyName,
                    companyAddress: $companyAddress,
                    companyEmail: $companyEmail,
                    companyWeb: $companyWeb
                })
                RETURN u
            """,
            companyId=companyId, companyName=companyName, companyAddress=companyAddress, companyEmail=companyEmail, companyWeb=companyWeb).single()

        try:
            with self.driver.session() as session:
                result = session.write_transaction(add_company, companyId, companyName, companyAddress, companyEmail, companyWeb)

                company = result['u']

                payload = {
                    "companyName": company["companyName"],
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
            favorites = self.get_user_interest(tx, user_id)

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
            favorites = self.get_user_interest(tx, user_id)

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
            favorites = self.get_user_interest(tx, user_id)

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
    def find_by_id(self, companyId):

        def find_company_by_id(tx, companyId):

            cypher = """
            MATCH (m:Company {companyId: $companyId})
            RETURN m
            LIMIT 1
            """
            first = tx.run(cypher, companyId=companyId).single()

            if first == None:
                raise NotFoundException()

            print("Company by ID:", first)

            return first.get("company")

        with self.driver.session() as session:
            return session.read_transaction(find_company_by_id, companyId)
    # end::findById[]

    # tag::getSimilarCourses[]
    def get_similar_companies(self, companyId, limit=6, skip=0, user_id=None):
        # Get similar courses
        def find_similar_companies(tx, companyId, limit, skip, user_id):
            favorites = self.get_user_interest(tx, user_id)

            cypher = """
            MATCH (:Company {companyId: $companyId})-[:IN_GENRE|ACTED_IN|DIRECTED]->()<-[:IN_GENRE|ACTED_IN|DIRECTED]-(m)
            WHERE m.imdbRating IS NOT NULL

            WITH m, count(*) AS inCommon
            WITH m, inCommon, m.imdbRating * inCommon AS score
            ORDER BY score DESC

            SKIP $skip
            LIMIT $limit

            RETURN m {
                .*,
                score: score,
                favorite: m.tmdbId IN $favorites
            } AS movie
            """

            result = tx.run(cypher, companyId=companyId, limit=limit, skip=skip, favorites=favorites)

            return [ row.get("company") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(find_similar_companies, companyId, limit, skip, user_id)
    # end::getSimilarMovies[]

    # tag::getUserFavorites[]
    def get_user_interest(self, tx, user_id):
        if user_id == None:
            return []

        result = tx.run("""
            MATCH (u:User {userId: $userId})-[:INTERESTED_IN]->(m)
            RETURN m.tmdbId AS id
        """, userId=user_id)

        return [ record.get("id") for record in result ]
    # end::getUserFavorites[]
