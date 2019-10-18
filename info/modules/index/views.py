from info.utils.common import user_login_data
from . import index_blu
from info.models import *
from flask import render_template, session, current_app, jsonify, request, g
from info.response_code import *
from info.modules.passport import *


@index_blu.route('/')
@user_login_data
def index():
    # 1.获取到当前用户登录到的id
    # print("*"*50)
    # nick_name = session.get('nick_name')
    # user = None
    # if nick_name:
    #     try:
    #         user = User.query.filter_by(nick_name=nick_name).first()
    #         print(user.nick_name)
    #     except Exception as e:
    #         current_app.logger.error(e)

    # 使用g变量获取用户登录信息
    user = g.user
    # 2.右侧新闻排行(显示新闻排行列表)
    # 按照点击量排序查询点击量最高的前十条新闻
    try:
        click_news = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="点击排行数据不存在")
    new_dict = []
    # 按照对象字典添加到列表中(to_basik_dic())
    # news_dict = [news_object.to_basic_dic() for news_object in click_news]
    for news_object in click_news:
        click_news_dictionary = news_object.to_basic_dict()
        new_dict.append(click_news_dictionary)
    # 3.新闻分类
    # 获取新闻分类数据
    try:
        news_type = Category.query.order_by(Category.id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="新闻分类数据不存在")
    # 定义列表保存分类数据
    categories = [type_ca.to_dict() for type_ca in news_type]
    # news_type.append(categories)
    # 拼接内容
    data = {
            'user': user,
            'news_dict': new_dict,
            'category_list': categories
            }
    # 5.返回数据
    return render_template("news/index.html", data=data)


@index_blu.route('/news_list')
def new_list():
    """获取首页新闻数据"""
    # 1.获取参数,并指定默认为最新分类,第一页,一页显示十条内容
    # 页数,不传即获取第一页
    page = request.args.get("page", "1")
    # 每页多少条数据如果不传，默认十条
    per_page = request.args.get("page_per", "10")
    # 分类id
    cid = request.args.get("cid", "1")
    # 2.校验参数
    if not all([page, cid, per_page]):
        jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        page, per_page, cid = int(page), int(per_page), int(cid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="不存在数据")
    # 根据分类id,定义变量存储分类条件
    filters = [News.status == 0]
    # 如果分类id不为0，那么添加分类id的过滤
    if cid != 1:
        filters.append(News.category_id == cid)
    # filters = []
    # if cid > 1:
    #     filters.append(News.category_id == cid)
    # 默认选择最新数据分类,默认按照分类id进行过滤，按新闻发布时间进行排序，对查询数据进行分页
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    # 3.查询数据
    new_dict_list = []
    # 模型对象
    news_list = paginate.items
    # 总页数
    total_page = paginate.pages
    # 当前页数
    cur_page = paginate.page
    # 4.将模型对象列表转成字典列表
    for news_pro in news_list:
        new_dict_list.append(news_pro.to_dict())
    data = {
        'news_dict_list': new_dict_list,
        "total_page": total_page,
        'cur_page': cur_page
    }
    # 5.返回数据
    return jsonify(errno=RET.OK, errmsg='成功', data=data)


