# -*-coding:utf-8-*-
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask.templating import render_template
from configparser import ConfigParser
from flask_redis import FlaskRedis
from datetime import datetime, timedelta
import json
import os


# Flask对象
app = Flask(__name__)
redis_client = FlaskRedis(app, decode_responses=True)
socket = SocketIO()
socket.init_app(app)
basedir = os.path.abspath(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')
mission_number = int(config.get('EMAIL', 'mission_count'))


@app.route('/', methods=['GET'])
def filter_index():
    # 前台控制面板
    # 已完成总量
    filter_finish = int(redis_client.get('task_number')) - int(redis_client.scard('emails_data'))
    # 任务总量
    task_total_number = int(redis_client.scard('emails_data'))
    # 开始时间
    start_time = datetime.strptime(redis_client.get('start_time'), '%Y-%m-%d %H:%M:%S')
    now_time = datetime.now()
    # 任务耗时
    task_spend_time = str(now_time - start_time)
    task_spend_seconds = int((now_time - start_time).seconds)
    # 任务速度
    filter_speed = filter_finish / task_spend_seconds
    if filter_speed == 0:
        task_total_time = "NAV"
        task_finish_time = "NAV"
    else:
        task_total_time_seconds = task_total_number / filter_speed
        m, s = divmod(task_total_time_seconds, 60)
        h, m = divmod(m, 60)
        task_total_time = "%dH %02dmin" % (h, m)
        task_finish_time_obj = datetime.now() + timedelta(seconds=task_total_time_seconds)
        task_finish_time = task_finish_time_obj.strftime('%Y-%m-%d %H:%M:%S')
    finish_percent = filter_finish / int(redis_client.get('task_number'))
    filter_success = int(redis_client.scard('success_data'))
    auth_account_percent = filter_success / filter_finish
    return render_template(
        'index.html',
        filter_speed='%.2f/sec' % filter_speed,
        filter_finish=filter_finish,
        task_total_number=task_total_number,
        task_total_time=task_total_time,
        task_spend_time=task_spend_time,
        task_finish_time=task_finish_time,
        finish_percent='%.2f%%' % (finish_percent * 100),
        filter_success=filter_success,
        auth_account_percent='%.2f%%' % (auth_account_percent * 100),
    )


@app.route('/filter/', methods=['GET'])
def filter_server():
    data = redis_client.spop('emails_data', mission_number)
    return jsonify({
        'mission_emails': data,
        'emails_balance': redis_client.scard('emails_data')
    })


@app.route('/load_data/')
def loading():
    # 读取文件
    file = open('source/2600w.txt', 'r', encoding='utf-8')
    total_line_number = count_file_lines('source/2600w.txt')
    percent_number = int(total_line_number / 1000)
    temp = 1
    percent = 0
    redis_client.flushall()
    socket.emit(event='loading', data={'percent': percent})
    temp_data = []
    for line in file:
        temp_data.append(line.strip())
        if temp % percent_number == 0:
            with redis_client.pipeline(transaction=False) as p:
                for d in temp_data:
                    p.sadd('emails_data', d)
                p.execute()
            temp_data = list()
            percent = percent + 0.1
            redis_client.set('task_number', redis_client.scard('emails_data'))
            socket.emit(event='loading', data={'percent': '%.2f%%' % percent})
            socket.emit(event='task_number', data={'task_number': redis_client.scard('emails_data')})
        temp += 1
    with redis_client.pipeline(transaction=False) as p:
        for d in temp_data:
            p.sadd('emails_data', d)
        p.execute()
    socket.emit(event='loading', data={'percent': 100})
    redis_client.set('start_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    redis_client.set('task_number', redis_client.scard('emails_data'))
    redis_client.set('filter_number', 0)
    redis_client.set('success_number', 0)
    redis_client.set('total_line_number', total_line_number)
    return jsonify({
        'status': 'success',
        'count': temp
    })


@app.route('/load_random_data_seven_qq/')
def load_random_data():
    percent_number = 10000
    redis_client.flushall()
    socket.emit(event='loading', data={'percent': 0})
    temp = 0
    percent = 0
    temp_data = []
    for line in range(1000000, 10000000):
        temp_data.append(str(line) + '@qq.com')
        if temp % percent_number == 0:
            with redis_client.pipeline(transaction=False) as p:
                for d in temp_data:
                    p.sadd('emails_data', d)
                p.execute()
            temp_data = list()
            percent = percent + 0.1
            redis_client.set('task_number', redis_client.scard('emails_data'))
            socket.emit(event='loading', data={'percent': '%.2f%%' % percent})
            socket.emit(event='task_number', data={'task_number': redis_client.scard('emails_data')})
        temp += 1
    with redis_client.pipeline(transaction=False) as p:
        for d in temp_data:
            p.sadd('emails_data', d)
        p.execute()
    socket.emit(event='loading', data={'percent': 100})
    socket.emit(event='task_number', data={'task_number': redis_client.scard('emails_data')})
    redis_client.set('start_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    redis_client.set('task_number', redis_client.scard('emails_data'))
    return jsonify({
        'status': 'success',
        'count': temp
    })


@app.route('/result/', methods=['POST'])
def result_handler():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    emails = json_data.get('emails')
    result = open('results.txt', 'a+', encoding='utf-8')
    for line in emails:
        result.write(line + '\n')
    result.close()
    with redis_client.pipeline(transaction=False) as p:
        for d in emails:
            p.sadd('success_data', d)
        p.execute()
    # 前台控制面板
    # 已完成总量
    filter_finish = int(redis_client.get('task_number')) - int(redis_client.scard('emails_data'))
    # 任务总量
    task_total_number = int(redis_client.scard('emails_data'))
    # 开始时间
    start_time = datetime.strptime(redis_client.get('start_time'), '%Y-%m-%d %H:%M:%S')
    now_time = datetime.now()
    # 任务耗时
    task_spend_time = str(now_time - start_time)
    task_spend_seconds = int((now_time - start_time).seconds)
    # 任务速度
    filter_speed = filter_finish / task_spend_seconds
    task_total_time_seconds = task_total_number / filter_speed
    m, s = divmod(task_total_time_seconds, 60)
    h, m = divmod(m, 60)
    task_total_time = "%dH %02dmin" % (h, m)
    task_finish_time_obj = datetime.now() + timedelta(seconds=task_total_time_seconds)
    task_finish_time = task_finish_time_obj.strftime('%Y-%m-%d %H:%M:%S')
    finish_percent = filter_finish / int(redis_client.get('total_line_number'))
    filter_success = int(redis_client.scard('success_data'))
    auth_account_percent = filter_success / filter_finish
    socket.emit('filter_status', {
        'filter_speed': '%.2f/sec' % filter_speed,
        'filter_finish': filter_finish,
        'task_total_number': task_total_number,
        'task_total_time': task_total_time,
        'task_spend_time': task_spend_time,
        'task_finish_time': task_finish_time,
        'finish_percent': '%.2f%%' % (finish_percent * 100),
        'filter_success': filter_success,
        'auth_account_percent': '%.2f%%' % (auth_account_percent * 100),
    })
    return jsonify({'status': 'success'})

# @app.route('/filter_number/', methods=['GET'])
# def filter_dashboard():
#     # 每过滤100 返回一次
#     filter_number = int(redis_client.get('filter_number')) + 1
#     redis_client.set('filter_number', filter_number)
#     # 前台控制面板
#     filter_finish = filter_number * 100
#     task_total_number = int(redis_client.get('task_number'))
#     start_time = datetime.strptime(redis_client.get('start_time'), '%Y-%m-%d %H:%M:%S')
#     now_time = datetime.now()
#     task_spend_time = str(now_time - start_time)
#     task_spend_seconds = int((now_time - start_time).seconds)
#     filter_speed = filter_finish / task_spend_seconds
#     task_total_time_seconds = task_total_number / filter_speed
#     m, s = divmod(task_total_time_seconds, 60)
#     h, m = divmod(m, 60)
#     task_total_time = "%dH %02dmin" % (h, m)
#     task_finish_time_obj = datetime.now() + timedelta(seconds=task_total_time_seconds)
#     task_finish_time = task_finish_time_obj.strftime('%Y-%m-%d %H:%M:%S')
#     finish_percent = filter_finish / int(redis_client.get('total_line_number'))
#
#     socket.emit('filter_status', {
#         'filter_speed': '%.2f/sec' % filter_speed,
#         'filter_finish': filter_finish,
#         'task_total_number': task_total_number,
#         'task_total_time': task_total_time,
#         'task_spend_time': task_spend_time,
#         'task_finish_time': task_finish_time,
#         'finish_percent': '%.2f%%' % (finish_percent * 100)
#     })
#     return jsonify({'status': 200})
#
#
# @app.route('/success_number/', methods=['GET'])
# def success_dashboard():
#     # 每过滤100 返回一次
#     success_number = int(redis_client.get('success_number')) + 1
#     redis_client.set('success_number', success_number)
#     # 前台控制面板
#     filter_success = success_number * 100
#     filter_number = int(redis_client.get('filter_number'))
#     auth_account_percent = filter_success / (filter_number * 100)
#     task_number = redis_client.scard('emails_data')
#     socket.emit('success_status', {
#         'filter_success': filter_success,
#         'auth_account_percent': '%.2f%%' % (auth_account_percent * 100),
#         'task_number': task_number,
#     })
#     return jsonify({'status': 200})


def count_file_lines(filename):
    count = 0
    fp = open(filename, "rb")
    byte_n = bytes("\n", encoding="utf-8")
    while True:
        buffer = fp.read(16*1024*1024)
        if not buffer:
            count += 1  # 包含最后一行空行 ''
            break
        count += buffer.count(byte_n)
    fp.close()
    return count


if __name__ == '__main__':
    socket.run(app, debug=True, host='0.0.0.0', port=5004)
