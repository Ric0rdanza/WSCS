To run this program, you need to install flask, flask-restful, and pyjwt.

The authorization server is authorization.py, running on 127.0.0.1:5001
The URL shortener server is main.py, running on 127.0.0.1:5000

To start the service, open two terminals and run 'python3 main.py' and 'python3 authorization.py' separately.


127.0.0.1:5000/test is used to check the whole picture of the storage of shortened URL and its corresponding long URL and the owner of the mapping. This service is not developed for users.
