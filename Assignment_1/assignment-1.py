from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

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


# {Shortened_url : {url: Original_url}}
map_url = {}

parser = reqparse.RequestParser()
parser.add_argument("url", location = "form")

def abort_if_todo_doesnt_exist(short_url):
	if short_url not in map_url:
		abort(404, message="Short url " + short_url + " doesn't exist")

class Todo(Resource):
	# e.g. 127.0.0.1:5000/map_url/short_url
	# Retrieve original url from short url given
	def get(self, short_url):
		abort_if_todo_doesnt_exist(short_url)
		return map_url[short_url], 301

	# Delete a shortened url
	def delete(self, short_url):
		abort_if_todo_doesnt_exist(short_url)
		del map_url[short_url]
		return '', 204

	# Update url map
	def put(self, short_url):
		args = parser.parse_args()
		task = {'url': args['url']}
		map_url[short_url] = task
		return task, 200

class TodoList(Resource):
	# e.g. 127.0.0.1:5000/map_url
	# Retrieve all url map
	def get(self):
		return map_url

	# Create shortened url
	def post(self):
		args = parser.parse_args()
		short_url = get_hash_key(args['url'])
		#short_url = int(max(map_url.keys()).lstrip('todo')) + 1
		short_url = short_url[0]# For test
		map_url[short_url] = {'url': args['url']}
		return map_url[short_url], 201

# flask route
api.add_resource(TodoList, '/map_url')
api.add_resource(Todo, '/map_url/<short_url>')

if __name__ == "__main__":
	app.run(debug = True)