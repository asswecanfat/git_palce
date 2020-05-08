from flask_uploads import UploadNotAllowed

from . import main
from .form import PostForm
from .. import db, photos
from ..models import Stu
from ... import all_config

from flask import render_template, abort, request, make_response
from datetime import datetime, timedelta
from pathlib import Path
from .file_deal import deal_hash, get_time

user_dict = {}
user_insure = []
end_time = datetime.now()
flag = 0
TbModel = object


@main.route('/signIn', methods=['POST', 'GET'])
def sign_in():
    global user_dict
    global end_time
    global flag
    global TbModel
    global user_insure
    form = PostForm()
    if request.method == 'GET':
        u_name, s_id = request.cookies.get('value', default='+').split('+')
        form.username.process_formdata([u_name])
        form.student_id.process_formdata([s_id])
    message = ''
    if not flag:
        abort(404)
    if datetime.now() > end_time:
        flag = 0
        abort(404)
    if form.validate_on_submit() and 'photo' in request.files:
        form_data = request.form
        user_name = form_data['username']
        user_id = form_data['student_id']
        if user_id in user_insure:
            message = '您已签到！无需重复签到！'
        else:
            if user_dict.get(user_id) == user_name:
                img_file = request.files['photo']
                file_type = Path(img_file.filename).suffix
                img_name = '{}{}'.format(deal_hash(str(Path(f'{user_id}{user_name}')) + str(datetime.today())),
                                         file_type)
                try:
                    data = TbModel()
                    setattr(data, 'id', user_id)
                    setattr(data, 'name', user_name)
                    setattr(data, 'time', str(datetime.today()))
                    setattr(data, 'url', f'http://{all_config.ip}/pic_show/{img_name}')
                    db.session.add(data)
                    photos.save(storage=img_file, name=str(img_name))
                    db.session.commit()
                except UploadNotAllowed:
                    db.session.rollback()
                    message = '签到失败，数据记录错误(文件类型错误)！'
                else:
                    message = '签到成功！'
                    user_insure.append(user_id)
                    res = make_response(render_template('index.html',
                                                        form=form,
                                                        message=message,
                                                        time=get_time(end_time)))
                    res.set_cookie('value', f'{user_name}+{user_id}', max_age=30)
                    return res
            else:
                message = '签到失败，学号与姓名不匹配！'
    return render_template('index.html',
                           form=form,
                           message=message,
                           time=get_time(end_time))


@main.route('/pic_show/<string:img_name>', methods=['POST', 'GET'])
def show(img_name):
    return render_template('show.html', img_url=f'../static/data/{img_name}')


@main.before_app_first_request
def creat():
    global user_dict
    user_list = Stu.query.all()
    user_dict = {str(i.id): i.name for i in user_list}


@main.route('/start/<string:course>', methods=['POST', 'GET'])
def start(course):
    global TbModel
    global end_time
    global flag
    global user_insure
    tb_name = f'{str(datetime.now().date())}{course}'
    num = db.Column('num', db.Integer, autoincrement=True, primary_key=True, nullable=False)
    id_ = db.Column('id', db.BIGINT)
    name = db.Column('name', db.String(64))
    time = db.Column('time', db.DATETIME)
    url = db.Column('url', db.String(255))
    table = db.Table(tb_name, db.metadata, num, id_, name, time, url)
    db.metadata.create_all(bind=db.engine, tables=[table])
    '''
        动态建表
    '''
    # 将一个类和table映射一下：
    # 根据tb_name构造一个类名
    class_name = tb_name.title().replace('_', '') + 'Model'
    # 创建类，必须为空类
    TbModel = type(class_name, (object,), {
    })
    db.mapper(TbModel, table)
    TbModel.query = db.session.query(TbModel)
    flag = 1
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=20)
    user_insure = []
    return '200'
