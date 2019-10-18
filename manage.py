from flask import current_app
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from info import create_app, db, models

# manage.py 是程序的启动入口,只关心启动得相关参数以及内容
# 通过指定的名字创建对应配置的app
# 指定环境
from info.models import User

app = create_app('development')
manager = Manager(app)
# 将app与db关联
Migrate(app, db)
# 将迁移命令添加到manager中
manager.add_command('db', MigrateCommand)

# 通过命令行创建管理员账号
@manager.option('-u', '-name', dest="name")
@manager.option('-p', '-password', dest="password")
def createsuperuser(name, password):
    if not all([name, password]):
        print("参数不足")
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
    print("****************添加成功*******************************")


if __name__ == '__main__':
    manager.run()