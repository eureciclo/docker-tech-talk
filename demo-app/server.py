from redis import Redis
from klein import run, route

@route('/')
def home(request):
    return 'Hello, world!'

@route('/redis')
def redis(request):
    client = Redis.from_url("redis://redis/0")
    redis_working = client.ping()
    response = ''
    if redis_working:
        response = 'PONG'
    else:
        raise BaseException('Redis not working properly.')

    return 'Sent PING server -> Redis. <br/> Received ' + response + ' server <- Redis.'

run("0.0.0.0", 5000)