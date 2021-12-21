from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.functional import wraps
from .models import AuthForm
from passlib.hash import pbkdf2_sha256
import jwt
import datetime
import pymongo


app = {}
app['SECRET_KEY'] = 'thisisthesecretkey'

client = pymongo.MongoClient("mongodb://localhost:27017/")  # connect to db
db = (
    client.user_tokens
)

# Create your views here.

# curl -d "token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjpudWxsLCJleHAiOjE2NDAwNzM2NDh9.2zxoyhd3ovA6rBPTRCdKw1OZV-7wQfsiZHvh8teWkNE
def check_for_token(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        token = request.POST.get('token')
        if not token:
            return JsonResponse({'message': 'Missing Token!'}), 401
        try:
            data = jwt.decode(token, app['SECRET_KEY'], algorithms=["HS256"])
        except:
            return JsonResponse({'Message': 'Invalid Token'})
        return func(*args, **kwargs)
    return wrapped

def index(request):
    request.session['logged_in'] = False
    if not request.session.get('logged_in'):
        return render(request, 'login.html')
    else:
        print(request.session)
        return "Currently Not Logged In"

def public(request):
    return JsonResponse({'Success': "Anyone can view this"})

@check_for_token
@csrf_exempt
def auth(request):
    if request.method == 'POST':
        return JsonResponse({'Success': "Only Viewable with a token"})
    if request.method == 'GET':
        return JsonResponse({'Success': "GOTTEN"})


def login(request):
    if request.method == 'POST':
        user = db.user_tokens.find_one({"email": request.POST.get("email")})
        if user == None:
            password = pbkdf2_sha256.encrypt(request.POST.get('password'))
            request.session['logged_in'] = True
            token = jwt.encode({'user': request.POST.get('username'),
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)},
                                app['SECRET_KEY'])
            db.user_tokens.insert_one({"email": request.POST.get("email"), 'password': password, 'token': {str(datetime.datetime.utcnow()): token}})

            return JsonResponse({'Success': 'You have been Registered', 'token': token})

        elif user != None:
            if user['email'] == request.POST.get("email") and pbkdf2_sha256.verify(request.POST.get('password'), user['password']):
                request.session['logged_in'] = True
                token = jwt.encode({'user': request.POST.get('username'),
                                    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30)},
                                    app['SECRET_KEY'])
                db.user_tokens.update({"email": request.POST.get("email")}, {'$set': {'token.{}'.format(datetime.datetime.utcnow()): token}})
                print(datetime.datetime.utcnow() + datetime.timedelta(seconds=30))
                return JsonResponse({'New Token Created': token})
            else:
                return JsonResponse({'Error': 'Email Does Not Corresponds to Password'})
        else:
            return  JsonResponse({'Error': "Not Found"})
