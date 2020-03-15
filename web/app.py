from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.usersDatabase
users_col = db["users"]
users_col.drop()

nlp_lg = spacy.load('en_core_web_lg')
nlp_sm = spacy.load('en_core_web_sm')

def check_credentials_format(posted_data):
    if "username" not in posted_data or "password" not in posted_data:
        return 301
    if type(posted_data["username"]) not in [str] or type(posted_data["password"]) not in [str]:
        return 302
    return 200


def check_password(posted_data):
    username = posted_data["username"]
    if username not in users_col.distinct("username"):
        return 310
    encoded_password = users_col.find({"username": username})[0]["password"]
    if not bcrypt.checkpw(posted_data["password"].encode('utf8'), encoded_password):
        return 311
    return 200


def check_documents_format(posted_data):
    if "doc1" not in posted_data or "doc2" not in posted_data:
        return 301
    if type(posted_data["doc1"]) not in [str] or type(posted_data["doc2"]) not in [str]:
        return 302
    return 200


class Register(Resource):
    def post(self):
        posted_data = request.get_json()
        status_code = check_credentials_format(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Problem with credentials format",
                "Status Code": status_code
            })

        username = posted_data['username']
        password = posted_data['password']
        l_users = users_col.distinct("username")
        if username in l_users:
            return jsonify({
                "Message": "User already exists",
                "Status Code": 303
            })

        salt = bcrypt.gensalt(10)
        hashed = bcrypt.hashpw(password.encode('utf8'), salt)

        users_col.insert({"username": username, "password": hashed, "tokens": 10})

        return jsonify({
            "Status Code": 200,
            "Message": "User registerd succesfully"
        })


class CompareSmall(Resource):
    def post(self):
        posted_data = request.get_json()
        status_code = check_credentials_format(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Problem with credentials format",
                "Status Code": status_code
            })
        status_code = check_password(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Incorrect credentials",
                "Status Code": status_code
            })
        status_code = check_documents_format(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Problem with documents format",
                "Status Code": status_code
            })

        username = posted_data["username"]
        tokens = users_col.find({"username": username})[0]["tokens"]
        if tokens <= 0:
            return jsonify({
                "Message": "Not enough tokens",
                "Status Code": 330
            })

        tokens -= 1
        users_col.update({"username": username}, {"$set": {"tokens": tokens}})

        text1 = nlp_sm(posted_data['doc1'])
        text2 = nlp_sm(posted_data['doc2'])

        return jsonify({
            "Message": "[{}] Similarity: {}".format(tokens, str(text1.similarity(text2))),
            "Status Code": 200
        })

class CompareLarge(Resource):
    def post(self):
        posted_data = request.get_json()
        status_code = check_credentials_format(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Problem with credentials format",
                "Status Code": status_code
            })
        status_code = check_password(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Incorrect credentials",
                "Status Code": status_code
            })
        status_code = check_documents_format(posted_data)
        if status_code != 200:
            return jsonify({
                "Message": "Problem with documents format",
                "Status Code": status_code
            })

        username = posted_data["username"]
        tokens = users_col.find({"username": username})[0]["tokens"]
        if tokens <= 0:
            return jsonify({
                "Message": "Not enough tokens",
                "Status Code": 330
            })

        tokens -= 1
        users_col.update({"username": username}, {"$set": {"tokens": tokens}})

        text1 = nlp_lg(posted_data['doc1'])
        text2 = nlp_lg(posted_data['doc2'])

        return jsonify({
            "Message": "[{}] Similarity: {}".format(tokens, str(text1.similarity(text2))),
            "Status Code": 200
        })


api.add_resource(Register, '/register')
api.add_resource(CompareSmall, '/compare_s')
api.add_resource(CompareLarge, '/compare_l')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000", debug=True)


