from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource

import requests
import re
import hashlib

app = Flask(__name__)
api = Api(app)

# Shortener with md5
def get_md5(s):
	s = s.encode("utf8")
	m = hashlib.md5()
	m.update(s)
	return m.hexdigest()

code_map = (  
	'a' , 'b' , 'c' , 'd' , 'e' , 'f' , 'g' , 'h' ,  
	'i' , 'j' , 'k' , 'l' , 'm' , 'n' , 'o' , 'p' ,  
	'q' , 'r' , 's' , 't' , 'u' , 'v' , 'w' , 'x' ,  
	'y' , 'z' , '0' , '1' , '2' , '3' , '4' , '5' ,  
	'6' , '7' , '8' , '9' , 'A' , 'B' , 'C' , 'D' ,  
	'E' , 'F' , 'G' , 'H' , 'I' , 'J' , 'K' , 'L' ,  
	'M' , 'N' , 'O' , 'P' , 'Q' , 'R' , 'S' , 'T' ,  
	'U' , 'V' , 'W' , 'X' , 'Y' , 'Z'  
) 

def get_hash_key(long_url):  
    hkeys = []  
    hex = get_md5(long_url)  
    for i in range(0, 4):  
        n = int(hex[i*8:(i+1)*8], 16)  
        v = []  
        e = 0  
        for j in range(0, 5):  
            x = 0x0000003D & n  
            e |= ((0x00000002 & n ) >> 1) << j  
            v.insert(0, code_map[x])  
            n = n >> 6  
        e |= n << 5  
        v.insert(0, code_map[e & 0x0000003D])  
        hkeys.append(''.join(v))  
    return hkeys 

# {Shortened_url : 
#		{Original_url: 
#			{owner: [Usernames]}
#		}, 
#		{Modified_url:
#			{owner: [Usernames]}
#		}
# }
map_url = {}

parser = reqparse.RequestParser()

parser.add_argument("url", location = "form")

def is_url(candidate):
	schema = ["http", "https", "ftp"]
	mark = "://"
	if mark not in candidate:
		return False
	search_obj = re.search("(.*)://(.*)", candidate, re.M|re.I)
	if search_obj.group(1) not in schema:
		return False
	if search_obj.group(2)[:-1] == ".":
		return False
	if "." not in search_obj.group(2):
		return False
	return True

# Send a request to login server to varify that token is correct
def is_token_valid(token):
	data = {"Authorization": token}
	username = requests.post("http://127.0.0.1:5001/verify", headers = data)
	if username.status_code == 200:
		uid = username.text
		return uid
	else:
		return False

class WithId(Resource):
	# e.g. 127.0.0.1:5000/<shortened url>
	# Retrieve original url from short url given
	def get(self, id):
		if id not in map_url:
			return "error", 404
		url = []
		for key in map_url[id]:
			url.append(key)
		return url, 301

	# Delete a shortened url
	def delete(self, id):
		# check the correctness of the token
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return "forbidden", 403
		uid = is_token_valid(token)
		if not uid:
			return "forbidden", 403
		# short url not exists
		if id not in map_url:
			return "error", 404
		# find the url user want to delete
		url_to_be_deleted = ""
		for key in map_url[id]:
			if uid in map_url[id][key]["owner"]:
				url_to_be_deleted = key
		# delete
		if url_to_be_deleted == "":
			return "forbidden", 403
		else:
			if len(map_url[id][url_to_be_deleted]["owner"]) > 1:
				# more than one user owned the mapping
				map_url[id][url_to_be_deleted]["owner"].remove(uid)
			else:
				# only one user owned the mapping
				del map_url[id][url_to_be_deleted]
		if not map_url[id]:
			del map_url[id]
		return '', 204

	# Update a url
	def put(self, id):
		# check correctness of given url
		if id not in map_url:
			return "error", 404
		args = parser.parse_args()
		if not is_url(args['url']):
			return "error", 400
		# verify the token
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return "forbidden", 403
		uid = is_token_valid(token)
		if not uid:
			return "forbidden", 403
		# find url to be modified
		url_to_be_modified = ""
		for key in map_url[id]:
			if uid in map_url[id][key]["owner"]:
				url_to_be_modified = key
		# modify
		if url_to_be_modified == "":
			return "forbidden", 403
		else:
			# remove the user from owner of original url
			if len(map_url[id][url_to_be_modified]["owner"]) > 1:
				map_url[id][url_to_be_modified]["owner"].remove(uid)
			else:
				del map_url[id][url_to_be_modified]
		# create a new mapping or add username to existing mapping
		if args['url'] in map_url[id]:
			map_url[id][args['url']]["owner"].append(uid)
		else:
			task = {args['url']: {"owner": [uid]}}
			map_url[id].update(task)
		return id, 200

class WithoutId(Resource):
	# e.g. 127.0.0.1:5000/
	# Retrieve all url map of user
	def get(self):
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return "forbidden", 403
		uid = is_token_valid(token)
		if not uid:
			return "forbidden", 403
		result = {}
		for key_short in map_url:
			for key_long in map_url[key_short]:
				if uid in map_url[key_short][key_long]["owner"]:
					result.update({key_short: key_long})
					break

		return result, 200

	# Create shortened url
	def post(self):
		args = parser.parse_args()
		# verify the token
		uid = ""
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return 403
		uid = is_token_valid(token)
		if not uid:
			return 403
		# check correctness of given url
		if not is_url(args['url']):
			return "error", 400
		short_url = get_hash_key(args['url'])
		short_url = short_url[0]# pick the first piece for test

		if short_url in map_url:
			# short url already exists
			if args["url"] in map_url[short_url]:
				# if the mapping has not been modified
				if uid in map_url[short_url][args["url"]]["owner"]:
					# user already owned the url
					return short_url, 201
				else:
					# user not owned the url
					map_url[short_url][args["url"]]["owner"].append(uid)
					return short_url, 201
			else:
				# the mapping has been modified before
				for key in map_url[short_url]:
					# if the user sending request modified the mapping, forbidden
					if uid in map_url[short_url][key]["owner"]:
						return "forbidden", 403
				# create a new mapping
				map_url[short_url].update({args["url"]: {"owner": [uid]}})
				return short_url, 201
		else:
			# short url not exists, create a mapping
			map_url[short_url] = {args['url']: {"owner": [uid]}}
			return short_url, 201
	# Delete all mapping of a user
	def delete(self):
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return "forbidden", 403
		uid = is_token_valid(token)
		if not uid:
			return "forbidden", 403
		delete_list = []
		for key_short in map_url:
			for key_long in map_url[key_short]:
				# check the ownership
				if uid in map_url[key_short][key_long]["owner"]:
					if len(map_url[key_short][key_long]["owner"]) > 1:
						map_url[key_short][key_long]["owner"].remove(uid)
					else:
						del map_url[key_short][key_long]
					if not map_url[key_short]:
						delete_list.append(key_short)
						map_url[key_short].clear()
				break
		for i in delete_list:
			del map_url[i]
		return "", 404

class Test(Resource):
	def get(self):
		return map_url, 200
# flask route
api.add_resource(WithoutId, '/')
api.add_resource(WithId, '/<id>')

api.add_resource(Test, '/test')

if __name__ == "__main__":
	app.run(debug = True)