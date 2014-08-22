import hashlib

def get_hashed_password(password, salt="somesalt"):
    return hashlib.sha512(password + salt).hexdigest()