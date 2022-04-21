from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
import jwt

secret = "random_string"

app = Flask(__name__)
api = Api(app)

# users = {username: password}
users = {}

parser = reqparse.RequestParser()

parser.add_argument("username", location = "form")
parser.add_argument("password", location = "form")

def encode(json):
    token = jwt.encode(json, secret, algorithm = "HS256")
    return token

def decode(token):
    try:
        json = jwt.decode(token, secret, algorithms = ["HS256"])
    except:
        json = {}
    finally:
        return json

class Signup(Resource):
    def post(self):
        args = parser.parse_args()
        if not args["username"] or not args["password"]:
            return "error", 403
        if args["username"] in users:
            return "Username already exsits", 200
        users[args["username"]] = args["password"]
        return 200

class Login(Resource):
    def post(self):
        args = parser.parse_args()
        if not args["username"] or not args["password"]:
            return "error", 403
        if users[args["username"]] == args["password"]:
            return encode(args), 200
        return "incorrect username or password", 401

# Used to check correctness of token
class Status(Resource):
    def post(self):
        token = ""
        print(request.headers)
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(' ')[1]
        args = decode(token)
        if "username" not in args:
            return 403
        if users[args["username"]] == args["password"]:
            return args["username"], 200
        return 401
    
api.add_resource(Signup, '/users')
api.add_resource(Login, '/users/login')
api.add_resource(Status, '/verify')

if __name__ == "__main__":
    app.run(port = 5001, debug = True)