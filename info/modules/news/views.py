from flask import render_template, g, jsonify, abort, request, current_app, session


from info.models import *
from info.modules.news import news_blu
from info.response_code import RET
from info.utils.common import user_login_data


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = g.user
    # 查询新闻
    news = News.query.get(news_id)
    # 检验报404错误
    if not news:
        abort(404)
    # 进入详情页后要更新新闻的点击次数
    category = Category.query.all()
    if not category:
        return jsonify(errno=RET.DBERR, errmsg="数据不存在")
    news.clicks += 1
    click_news = News.query.order_by(News.content).limit(constants.CLICK_RANK_MAX_NEWS).all()
    # 获取当前新闻最新的评论,按时间排序
    comments = Comment.query.filter(Comment.news_id == news.id).order_by(Comment.create_time.desc()).limit(10).all()
    # 判断是否收藏该新闻
    is_collected = False
    if user and news in user.collection_news:
        is_collected = True
    # 当前登录用户是否关注当前新闻作者
    is_followed = False
    # 判断用户是否收藏过该新闻
    if news.user and user:
        if news.user in user.followed:
            is_followed = True

    # 遍历评论id，将评论属性赋值
    comments_dict_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        # 为评论增加‘is—like’字段，判断是否评论
        comment_dict['is_like'] = False
        # 判断用户是否在点赞评论里面
        if comment.id in comments_dict_list:
            comment_dict['is_like'] = True
        comments_dict_list.append(comment_dict)
        print(click_news,1111111111111111111111111111111111)
    data = {
        "user": user.to_dict() if user else None,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "is_followed": is_followed,
        "news_dict": click_news,
        "comments": comments_dict_list
            }
    return render_template('news/detail.html', data=data)


@news_blu.route('/news_collect', methods=["POST"])
@user_login_data
def news_collect():
    """新闻收藏"""
    user = g.user
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get("action")
    # 判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET, errmsg="参数不全")
    # action在不在指定的两个值：”collect“,"cancal_collect"内
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg="不在指定的值里面")
    # 查询新闻判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库不存在")
    # 收藏/取消收藏
    if action == "cancel_collect":
        if news in user.collection_news:
            try:
                user.collection_news.remove(news)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="取消收藏失败")
    else:
        if news not in user.collection_news:
            user.collection_news.append(news)
    return jsonify(errno=RET.OK, errmsg="success")


@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def add_news_comment():
    """添加评论"""
    # 用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.PARAMERR, errmsg="请先登录")
    # 获取参数
    # 新闻id
    news_id = request.json.get("news_id")
    # 评论内容
    comment = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    # 判断参数是否正确
    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="强转失败")
    if parent_id:
        parent_id = int(parent_id)
    # 查询新闻是否存在并校验
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg="新闻不存在")
    # 初始化评论模型，保存数据
    comment_init = Comment()
    comment_init.user_id = user.id
    comment_init.news_id = news_id
    comment_init.content = comment
    if parent_id:
        comment_init.parent_id = parent_id
    try:
        db.session.add(comment_init)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        # return jsonify(errno=RET.DBERR, errmsg="评论模型保存失败")
    # 配置文件设置了自动提交,自动提交要在return返回结果以后才执行commit命令,
    # 如果有回复评论id,再手动commit，否则无法回复评论内容
    # 返回响应
    return jsonify(errno=RET.OK, errmsg="success", data=comment_init.to_dict())


@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    """评论点赞"""
    # 用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.PARAMERR, errmsg="请登录")
    # 取到请求参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    # 判断参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg="数据不存在")
    try:
        comment_id = int(comment_id)
        print(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="强转失败")
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="数据不存在")

    # action的状态，如果点赞，则查询后将用户id和评论id添加到数据库
    if action == "add":
        # 使用CommentLike进行过滤查询
        comment_like_models = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                       CommentLike.comment_id == comment.id).first()
        print(comment_like_models, 55)
        if not comment_like_models:
            # 点赞评论
            # 获取到要被点赞的评论模型
            comment_like_models = CommentLike()
            comment_like_models.comment_id = comment.id
            comment_like_models.user_id = user.id
            try:
                db.session.add(comment_like_models)
                db.session.commit()
                # 更新点赞次数
                comment.like_count += 1
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.PARAMERR, errmsg="添加点赞id失败")
        # 取消点赞评论，查询数据库，如果已点赞，则删除点赞信息
        else:
            db.session.delete(comment_like_models)
        # 更新点赞次数
            comment.like_count -= 1
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="sussess")


@news_blu.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    """关注或者取消关注用户"""
    # 获取自己登录信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录")
    # 获取参数
    user_id = request.json.get("user_id")
    action = request.json.get("action")
    # 判断参数
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 获取要被关注的用户
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not other:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")
    if other.id == user.id:
        return jsonify(errno=RET.PARAMERR, errmsg="请勿关注自己")
    # 根据要执行的操作去修改对应的数据
    if action == "follow":
        if other not in user.followed:
            # 当前用户的关注列表添加一个值
            user.followed.append(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前用户已被关注")
    else:
        # 取消关注
        if other in user.followed:
            user.followed.remove(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前用户未被关注")
    return jsonify(errno=RET.OK, errmsg="操作成功")