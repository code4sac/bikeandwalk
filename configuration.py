## Base Settings

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "somereallylongstringtouseasakey"
    
    DATABASE = "bikeandwalk.sqlite"
    DATABASE_PATH_PREFIX = '/Users/bleddy/Sites/bikeandwalk.org/app/'
    DATABASE_URI = 'sqlite:///' + DATABASE_PATH_PREFIX + DATABASE
    
    # set session expiration in seconds
    PERMANENT_SESSION_LIFETIME = 60*20
    
    # Email Sending...
    SMTP_HOST = ""
    SMTP_PORT = ""
    SMTP_USER = ""
    SMTP_PASSWORD = ""
    
    # Uploads ...
    MAX_CONTENT_LENGTH = 300000
    
    # Persona settings
    PERSONA_JS='https://login.persona.org/include.js'
    PERSONA_VERIFIER='https://verifier.login.persona.org/verify'
    
class ProductionConfig(Config):
    pass
    
class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    

