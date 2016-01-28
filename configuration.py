## Base Settings

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "somereallylongstringtouseasakey"
    
    DATABASE = "bikeandwalk.sqlite"
    DATABASE_PATH_PREFIX = '/Users/bleddy/Sites/app.bikeandwalk.org/'
    DATABASE_URI = 'sqlite:///' + DATABASE_PATH_PREFIX + DATABASE
    
    # set session expiration in seconds
    PERMANENT_SESSION_LIFETIME = 60*20
    
    # Email Sending...
    ## Flask_Mail defaults
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = None
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = TESTING
    MAIL_ASCII_ATTACHMENTS = False
    
    # Uploads ...
    MAX_CONTENT_LENGTH = 300000
    
    # Persona settings
    PERSONA_JS='https://login.persona.org/include.js'
    PERSONA_VERIFIER='https://verifier.login.persona.org/verify'
    
    MAPBOX_PROJECT_ID = ""
    MAPBOX_ACCESS_TOKEN = ""
    
class ProductionConfig(Config):
    pass
    
class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    

