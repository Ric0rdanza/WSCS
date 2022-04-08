from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

import hashlib

app = Flask(__name__)
api = Api(app)

# 改成需要的操作
TODOS = {
	"todo1": {"task": "test task1"},
	"todo2": {"task": "test task2"},
	"todo3": {"task": "test task3"},
}

parser = reqparse.RequestParser()
parser.add_argument("task")

# 改下边的内容，应用url shortener
class Todo(Resource):
	# e.g. 127.0.0.1:5000/todos/todo1
	# Retrieve information
	def get(self, todo_id):
		abort_if_todo_doesnt_exist(todo_id)
		return TODOS[todo_id], 301

	# Delete information
	def delete(self, todo_id):
		abort_if_todo_doesnt_exist(todo_id)
		del TODOS[todo_id]
		return '', 204

	# Create information
	def put(self, todo_id):
		args = parser.parse_args()
		task = {'task': args['task']}
		TODOS[todo_id] = task
		return task, 200

class TodoList(Resource):
	# e.g. 127.0.0.1:5000/todos
	# Retrieve information
	def get(self):
		return TODOS

	# Update information
	def post(self):
		args = parser.parse_args()
		todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1
		todo_id = 'todo%i' % todo_id
		TODOS[todo_id] = {'task': args['task']}
		return TODOS[todo_id], 201

# flask route
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')




# 以下是url shortener所需操作
#url_map = {}

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

#print(get_hash_key("https://www.baidu.com/"))