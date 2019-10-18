from crypt import methods

from flask import g, jsonify, render_template, redirect, request, abort
from flask import current_app
from info import db
from info.constants import QINIU_DOMIN_PREFIX
from info.models import User, News, Category
from info.models import *
from .import profile_blue
from info.utils.common import user_login_data
from info.response_code import RET
from info.utils.image_storage import *


@profile_blue.route('/user_info')
@user_login_data
def user_info():
    # 如果用户登录则进入个人中心
    user = g.user
    if user:
        print(user.avatar_url, 1)
        return render_template('news/user.html', data={"user": user.to_dict()})
    # 如果没有登录,跳转主页
    else:
        return redirect('/')
    # 返回用户数据


@profile_blue.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
    """用户基本信息"""
    user = g.user
    # 如果是get请求,返回用户数据
    if request.method == "GET":
        return render_template('news/user_base_info.html', data={"user": user.to_dict()})
    # 修改用户数据
    # 获取传入参数
    #   签名
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")
    print(signature, nick_name, gender)
    # 校验参数
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    # 修改用户数据
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg='没有选择性别')
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据保存不完整')
    # 返回
    return jsonify(errno=RET.OK, errmsg='success')


@profile_blue.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    """头像上传"""
    user = g.user
    # 如果是get请求,返回用户数据
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', data={'user_info': user.to_dict()})
    # 1.获取到上传的图片
    avatar = request.files.get('avatar')
    if not avatar:
        return jsonify(errno=RET.PARAMERR, errmsg='没有获取到图片')
    data = avatar.read()
    # 2.上传头像
    # 使用自己封装的storage方法去进行图片上传
    image_name = storage(data)
    # 3.保存图像地址
    user.avatar_url = QINIU_DOMIN_PREFIX+'/'+image_name
    print(user.avatar_url)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片路径失败')
    # 拼接url返回数据
    return jsonify(errno=RET.OK, errmsg='success', data={'avatar_url': user.avatar_url})


@profile_blue.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    """修改密码"""
    user = g.user
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    # 1.获取参数
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    print(old_password, new_password)
    # 2.校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 3.判断旧密码是否正确
    if not user.check_password(old_password):
        return jsonify(errno=RET.PARAMERR, errmsg="旧密码错误")
    # 4.设置新密码
    user.password = new_password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='密码保存错误')
    # 5.返回
    return jsonify(errno=RET.OK, errmsg='success')


@profile_blue.route('/collection')
@user_login_data
def user_collection():
    """新闻收藏"""
    # 获取参数
    p = request.args.get('p', 1)
    p = int(p)
    # 判断参数
    if not p:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不存在')
    # 3.查询用户指定页数收藏的新闻
    user = g.user
    paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
    # 进行分页查询
    list_news = paginate.items
    # 当前页数
    cur_page = paginate.page
    # 总页数
    total_page = paginate.pages
    # 总数据
    # 收藏列表
    collection_news_list = [ne.to_dict() for ne in list_news]
    data = {'current_page': cur_page,
            'total_page': total_page,
            'collection': collection_news_list}
    # 返回注册
    return render_template('news/user_collection.html', data=data)


@profile_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    """新闻发布"""
    # GET请求
    user = g.user
    if request.method == 'GET':
        # 加载新闻分类
        type_new = Category.query.order_by(Category.id).all()
        categories = []
        for ty in type_new:
            if ty.id > 1:
                categories.append(ty)
        # 移除最新分类
        # 返回数据
        return render_template('news/user_news_release.html', data={'categories': categories})
    # 获取要提交的数据
    # 新闻标题
    title = request.form.get("title")
    # 新闻分类id
    category_id = request.form.get("category_id")
    # 新闻摘要
    digest = request.form.get('digest')
    # 索引图片
    index_image = request.files.get('index_image')
    # 新闻内容
    content = request.form.get('content')
    # 新闻来源
    source = request.form.get('source', "个人")
    print(title, category_id, digest, content)
    # 校验参数
    if not all([title, category_id, digest, content, index_image]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='强转失败')
    # 3.取到图片将图片上传到七牛云
    try:
        index_image_data = index_image.read()
        # 上传到七牛云
        key_image = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')
    # 保存数据
    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    # 个人发布
    news.user_id = user.id
    news.source = source
    news.index_image_url = QINIU_DOMIN_PREFIX+'/'+key_image
    # 新闻状态将新闻设置为1代表待审核状态
    news.status = 0
    # 手动设置新闻状态，在返回前commit提交
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="保存数据库失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg='success', data={"index_image_url": constants.QINIU_DOMIN_PREFIX+'/'+key_image})


@profile_blue.route('/news_list')
@user_login_data
def user_news_list():
    """新闻列表"""
    user = g.user
    p = request.args.get('p', 1)
    p = int(p)
    if not p:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不存在')
    paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
    news_list = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    news_list_li = [n.to_dict() for n in news_list]
    data = {'news_list': news_list_li,
            'current_page': current_page,
            'total_page': total_page}
    return render_template('news/user_news_list.html', data=data)


@profile_blue.route('/user_follow')
@user_login_data
def user_follow():
    """我的关注"""
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    user = g.user
    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据
        follows = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    user_dict_li = []
    for follow_user in follows:
        user_dict_li.append(follow_user.to_dict())
    data = {"users": user_dict_li,
            "total_page": total_page,
            "current_page": current_page
            }
    return render_template('news/user_follow.html', data=data)


@profile_blue.route('/other_info')
@user_login_data
def other_info():
    user = g.user
    # 去查询其他人的用户信息
    other_id = request.args.get('user_id')
    # 查询指定id用户信息
    if not other_id:
        abort(404)
    # 判断当前登录用户是否关注过该用户
    other = None
    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
    if not other:
        abort(404)
    is_followed = False
    if other and other:
        if other in user.followed:
            is_followed = True
    data = {
            'is_followed': is_followed,
            'user': user.to_dict() if user else None,
            'other_info': other
           }
    return render_template('news/other.html', data=data)


# @profile_blue.route('/other_news_list')
# def other_news_list():
#     """返回指定的用户发布的新闻"""
#     other_id = request.args.get('other_id')
#     p = request.args.get('p', 1)
#     try:
#         p = int(p)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
#     try:
#         other = User.query.get(other_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET, errmsg='数据库查询失败')
#     if not other:
#         return jsonify(errno=RET.NODATA, errmsg='当前用户不存在')
#     try:
#         paginate = other.news_list.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
#         # 获取当前页数据
#         news_li = paginate.items
#         # 当前页
#         current_page = paginate.page
#         # 总页数
#         total_page = paginate.pages
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
#     data = {'news_list': [n.to_dict() for n in news_li],
#             'total_page': total_page,
#             'current_page': current_page}
#     return jsonify(errno=RET.OK, errmsg='success', data=data)
#
#
#



