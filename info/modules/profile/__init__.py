from flask import Blueprint
profile_blue = Blueprint('profile', __name__, url_prefix='/profile')
from .import views