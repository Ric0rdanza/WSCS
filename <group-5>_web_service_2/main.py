from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource

import requests
import re
import hashlib

app = Flask(__name__)
api = Api(app)

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

def abort_if_todo_doesnt_exist(short_url):
	if short_url not in map_url:
		abort(404, message="Short url " + short_url + " doesn't exist")

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
		return map_url[id], 301

	# Delete a shortened url
	def delete(self, id):
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return 403
		data = {"Authorization": token}
		username = requests.post("http://127.0.0.1:5001/verify", headers = data)
		uid = username.text
		if id not in map_url:
			return "error", 404
		url_to_be_deleted = ""
		for key in map_url[id]:
			if uid in map_url[id][key]["owner"]:
				url_to_be_deleted = key
		if url_to_be_deleted == "":
			return "forbidden", 403
		else:
			if len(map_url[id][url_to_be_deleted]["owner"]) > 1:
				map_url[id][url_to_be_deleted]["owner"].remove(uid)
			else:
				del map_url[id][url_to_be_deleted]
		if not map_url[id]:
			del map_url[id]
		return '', 204

	# Update a url
	def put(self, id):
		if id not in map_url:
			return "error", 404
		args = parser.parse_args()
		if not is_url(args['url']):
			return "error", 400
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return "forbidden", 403
		uid = is_token_valid(token)
		if not uid:
			return "forbidden", 403
		url_to_be_modified = ""
		for key in map_url[id]:
			if uid in map_url[id][key]["owner"]:
				url_to_be_modified = key
		if url_to_be_modified == "":
			return "forbidden", 403
		else:
			if len(map_url[id][url_to_be_modified]["owner"]) > 1:
				map_url[id][url_to_be_modified]["owner"].remove(uid)
			else:
				del map_url[id][url_to_be_modified]
		if args['url'] in map_url[id]:
			map_url[id][args['url']]["owner"].append(uid)
		else:
			task = {args['url']: {"owner": [uid]}}
			map_url[id].update(task)
		return id, 200

class WithoutId(Resource):
	# e.g. 127.0.0.1:5000/
	# Retrieve all url map
	def get(self):
		return map_url, 200

	# Create shortened url
	def post(self):
		args = parser.parse_args()
		uid = ""
		token = ""
		if "Authorization" in request.headers:
			token = request.headers["Authorization"]
		else:
			return 403
		uid = is_token_valid(token)
		if not uid:
			return 403
		if not is_url(args['url']):
			return "error", 400
		short_url = get_hash_key(args['url'])
		short_url = short_url[0]# For test
		if short_url in map_url:
			if args["url"] in map_url[short_url]:
				if uid in map_url[short_url][args["url"]]["owner"]:
					return short_url, 201
				else:
					map_url[short_url][args["url"]]["owner"].append(uid)
					return short_url, 201
			else:
				map_url[short_url].update({args["url"]: {"owner": [uid]}})
				return short_url, 201
		else:
			map_url[short_url] = {args['url']: {"owner": [uid]}}
			return short_url, 201

	def delete(self):
		map_url.clear()
		return "", 404

# flask route
api.add_resource(WithoutId, '/')
api.add_resource(WithId, '/<id>')

if __name__ == "__main__":
	app.run(debug = True)