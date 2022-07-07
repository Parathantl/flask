import bcrypt
import jwt
from datetime import datetime

from flask import current_app

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException

from neo4j.exceptions import ConstraintError

class AuthDAO:

    def __init__(self, driver, jwt_secret):
        self.driver = driver
        self.jwt_secret = jwt_secret

    # tag::register[]
    def register(self, email, plain_password, firstName, lastName, contactNumber, description, fields):
        encrypted = bcrypt.hashpw(plain_password.encode("utf8"), bcrypt.gensalt()).decode('utf8')
        userId = firstName + email
        def create_user(tx, email, encrypted, firstName, lastName, contactNumber, description, userId):
            return tx.run("""
                CREATE (u:User {
                    userId: $userId,
                    email: $email,
                    password: $encrypted,
                    firstName: $firstName,
                    lastName: $lastName,
                    contactNumber: $contactNumber,
                    description: $description
                })
                RETURN u
            """,
            email=email, encrypted=encrypted, firstName=firstName, lastName=lastName, contactNumber=contactNumber,  description=description, userId=userId
            ).single()

        def add_field(tx, userId, fields):
            print("Pringint fields:", fields)
            for x in fields:
                tx.run("""
                    MATCH (u:User {
                        userId: $userId
                    })
                    MATCH (f:Field {
                        fieldId: $x['id']
                    })

                    MERGE (u)-[r:INTERESTED_IN]->(f)

                """, userId=userId, x=x).single()

        try:
            with self.driver.session() as session:
                result = session.write_transaction(create_user, email, encrypted, firstName, lastName, contactNumber, description, userId)

                user = result['u']


                fields_result = session.write_transaction(add_field, user["userId"], fields)

                payload = {
                    "userId": user["userId"],
                    "email":  user["email"],
                    "firstName":  user["firstName"],
                    "lastName": user["lastName"],
                }

                payload["token"] = self._generate_token(payload)

                return payload
        except ConstraintError as err:
            # Pass error details through to a ValidationException
            raise ValidationException(err.message, {
                "email": err.message
            })
    # end::register[]

    # tag::authenticate[]
    def authenticate(self, email, plain_password):
        def get_user(tx, email):
            # Get the result
            result = tx.run("MATCH (u:User {email: $email}) RETURN u",
                email=email)

            # Expect a single row
            first = result.single()

            # No records? Return None
            if first is None:
                return None

            # Get the `u` value returned by the Cypher query
            user = first.get("u")

            return user

        with self.driver.session() as session:
            user = session.read_transaction(get_user, email=email)

            # User not found, return False
            if user is None:
                return False

            # Passwords do not match, return false
            if bcrypt.checkpw(plain_password.encode('utf-8'), user["password"].encode('utf-8')) is False:
                return False

            # Generate JWT Token
            payload = {
                "userId": user["userId"],
                "email":  user["email"],
                "firstName":  user["firstName"],
                "lastName": user["lastName"]
            }

            payload["token"] = self._generate_token(payload)

            return payload
    # end::authenticate[]

    # tag::generate[]
    def _generate_token(self, payload):
        iat = datetime.utcnow()

        payload["sub"] = payload["userId"]
        payload["iat"] = iat
        payload["nbf"] = iat
        payload["exp"] = iat + current_app.config.get('JWT_EXPIRATION_DELTA')

        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm='HS256'
        ).decode('ascii')
    # end::generate[]

    # tag::decode[]
    def decode_token(auth_token, jwt_secret):
        try:
            payload = jwt.decode(auth_token, jwt_secret)
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    # end::decode[]
