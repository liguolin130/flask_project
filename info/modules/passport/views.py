
from flask import request, current_app, abort, make_response, session
from info import redis_store, constants, db
from info.models import *

from info.modules.passport import passport_blu
from info.response_code import RET
from info.utils.captcha.captcha import captcha
from flask import jsonify
import random, re


# /passport/image_code
@passport_blu.route('/image_code')
def get_image_code():
    """生成图片验证码"""
    # 1.获取参数
    image_code_id = request.args.get('image_Code')
    # 2.校验参数
    if not image_code_id:
        return jsonify(errno=RET.PARAMERR, errsmg="验证码错误")
    # 3.生成图片校验码
    name, text, image = captcha.generate_captcha()
    print("图片验证码为:%s" % text)
    # 4.保存图片校验码
    # 保存当前图片验证内容,并别设置过期时间
    redis_store.setex('imagecode'+image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    response = make_response(image)
    response.headers['Content-Type:'] = 'image/jpg'
    # 5.返回图片验证码
    return response


# 短信验证码
@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
    """发送短信的逻辑"""
    # 1.将前端参数转为字典
    # json_data = request.data
    # dict_data = json.loads(json_data)
    # dict_data = request.json
    # 手机号
    mobile = request.json.get('mobile')
    # 用户输入的图片验证内容
    image_code = request.json.get('image_code')
    # 真实图片验证编码
    image_code_id = request.json.get('image_code_id')
    print(mobile, image_code, image_code_id)
    # 2.校验参数(参数是否合格,判断是否有值)
    if not all([mobile, image_code, image_code_id]):
        # 先看参数存在与否,再判定参数是否正确
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # if not re.match(r"1[356789]\d{9}", mobile):
    #     return jsonify(errno=RET.PARAMERR, errmsg="号码错误")
    # 3.先从redis中取出真实的验证码内容
    try:
        real_image_code = redis_store.get('imagecode'+image_code_id)
        print("验证码取%s" % real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询不存在')
    # 4.与验证码内容进行对比,如果对比不一致返回验证码输入错误
    # 判断参数传过来的验证码,和你在第一个视图函数中的验证码数据是否相同
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='输入验证码错误')
    # 5.如果一致,生成短信验证码的内容(随机数据)
    sms_code_str = '%06d' % random.randint(0, 999999)
    print(sms_code_str)
    # 6.发送短信验证码
    # 保存验证码内容到redis
    try:
        redis_store.setex(mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code_str)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="保存错误")
    # 7.告知发送结果
    return jsonify(errno=RET.OK, errmsg='发送成功')


# 注册
@passport_blu.route('/register', methods=["POST"])
def register():
    """注册功能"""
    # 1.获取参数和判断参数是否有值
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password = request.json.get("password")
    # 2.从redis中获取指定手机号码对应的短信验证码
    phon_smscode = redis_store.get(mobile)
    print(phon_smscode, 123)
    # print(smscode, 12)
    # 3.校验校验码
    if phon_smscode != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")
    # 4.初始化user模型,设置数据并添加到数据库
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存错误")
    # 5.保存用户登录状态
    session["nick_name"] = mobile
    session["mobile"] = mobile
    # 6.返回注册结果
    print("---------success-------------------")
    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登录状态
@passport_blu.route('/login', methods=['POST'])
def login():
    """登录功能"""
    # 1.获取参数和判断是否有值
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    print(mobile, password, 1)

    if not all([mobile, password]):
        jsonify(errno=RET.PARAMERR, errmsg="参数不存在")
    # 2.从数据库查询出指定的用户
    user_new = User.query.filter(User.mobile == mobile).first()
    # password_new = User.query.filter(User.password_hash == password).first()
    print(user_new, 22)
    if not user_new:
        return jsonify(errno=RET.DBERR, errmsg="用户不存在")
    # 3.校验密码
    if not user_new.check_password(password):
        return jsonify(errno=RET.PARAMERR, errmsg="密码错误")
    # 4.保存用户登录状态
    session['user_id'] = user_new.id
    session['nick_name'] = user_new.mobile
    # 5.登陆成功返回
    # print('------------------login success-----------------------')
    return jsonify(errno=RET.OK, errmsg="登录成功")


# 登出
@passport_blu.route('/logout', methods=['POST'])
def logout():
    """清除sessio对应登录之后的信息"""
    session.clear()
# 返回结果
    return jsonify(errno=RET.OK, errmsg="退出成功")








