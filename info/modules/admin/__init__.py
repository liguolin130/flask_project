from flask import Blueprint, session, request, url_for, redirect

admin_blue = Blueprint('admin', __name__, url_prefix='/admin')

from . import view


@admin_blue.before_request
def check_admin():
    # 限制非管理员访问管理员页面
    is_admin = session.get('is_admin', False)
    if not is_admin and not request.url.endswith(url_for('admin.login')):
        return redirect('/')
