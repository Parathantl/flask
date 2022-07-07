from api.exceptions.notfound import NotFoundException

class MovieDAO:

    def __init__(self, driver):
        self.driver = driver

    # tag::all[]
    def all(self, sort, order, limit=6, skip=0, user_id=None):
        # TODO: Get list from movies from Neo4j
        return popular
    # end::all[]

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
    def find_by_id(self, id, user_id=None):
        # Find a movie by its ID
        def find_movie_by_id(tx, id, user_id = None):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
            MATCH (m:Movie {tmdbId: $id})
            RETURN m {
                .*,
                actors: [ (a)-[r:ACTED_IN]->(m) | a { .*, role: r.role } ],
                directors: [ (d)-[:DIRECTED]->(m) | d { .* } ],
                genres: [ (m)-[:IN_GENRE]->(g) | g { .name }],
                favorite: m.tmdbId IN $favorites
            } AS movie
            LIMIT 1
            """

            first = tx.run(cypher, id=id, favorites=favorites).single()

            if first == None:
                raise NotFoundException()

            return first.get("movie")

        with self.driver.session() as session:
            return session.read_transaction(find_movie_by_id, id, user_id)
    # end::findById[]

    # tag::getSimilarMovies[]
    def get_similar_movies(self, id, limit=6, skip=0, user_id=None):
        # Get similar movies
        def find_similar_movies(tx, id, limit, skip, user_id):
            favorites = self.get_user_favorites(tx, user_id)

            cypher = """
            MATCH (:Movie {tmdbId: $id})-[:IN_GENRE|ACTED_IN|DIRECTED]->()<-[:IN_GENRE|ACTED_IN|DIRECTED]-(m)
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

            result = tx.run(cypher, id=id, limit=limit, skip=skip, favorites=favorites)

            return [ row.get("movie") for row in result ]

        with self.driver.session() as session:
            return session.read_transaction(find_similar_movies, id, limit, skip, user_id)
    # end::getSimilarMovies[]

    # tag::getUserFavorites[]
    def get_user_favorites(self, tx, user_id):
        if user_id == None:
            return []

        result = tx.run("""
            MATCH (u:User {userId: $userId})-[:HAS_FAVORITE]->(m)
            RETURN m.tmdbId AS id
        """, userId=user_id)

        return [ record.get("id") for record in result ]
    # end::getUserFavorites[]
