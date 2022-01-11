from flask import Flask, jsonify, request, render_template
from common.mysql_operate import db
import tushare as ts
import re
import time
import json
import datetime
from loguru import logger

ts.set_token('df59bbfff559618c57346d99302a98c8f00d087dfcbf9a2271a66aac')
pro = ts.pro_api()
app = Flask(__name__, template_folder='../templates')
app.config["JSON_AS_ASCII"] = False  # jsonify返回的中文正常显示

INDEXS = dict()
"""
新股全局变量
{
    'cache_date':
    'new_stock_list'
}
"""
NEW_STOCKS = dict()

"""
新债全局变量
{
    'cache_date':
    'new_bond_list'
}
"""
NEW_BONDS = dict()

# 缓存数据
cache_data = {
    "东方财富":{
        "新股":{},
        "新债": {}
    },
    "同花顺":{
        "新股":{},
        "新债": {}
    }
}

def convert_date_to_date_int(dt):
    t = dt.year * 10000 + dt.month * 100 + dt.day
    return int(t)


def new_round(_float, _len):
    """
    Parameters
    ----------
    _float: float
    _len: int, 指定四舍五入需要保留的小数点后几位数为_len

    Returns
    -------
    type ==> float, 返回四舍五入后的值
    """
    if isinstance(_float, float):
        if str(_float)[::-1].find('.') <= _len:
            return(_float)
        if str(_float)[-1] == '5':
            return(round(float(str(_float)[:-1]+'6'), _len))
        else:
            return(round(_float, _len))
    else:
        return(round(_float, _len))

@app.route("/set_index", methods=['post'])
def set_index():
    if request.method == "POST":
        post_data = request.form.get('data')
        data = json.loads(post_data)
        if 'code' in data.keys():
            global INDEXS
            INDEXS[data['code']] = data

        return jsonify({"code": 0, "msg": "保存成功"})


@app.route("/get_index", methods=['get'])
def get_index():
    if request.method == "GET":
        code = request.args.get("code")
        global INDEXS
        if code in INDEXS.keys():
            return jsonify({"code": 0, "data": INDEXS[code], "msg": "查询成功"})
        else:
            return jsonify({"code": 1, "msg": "指数代码数据不存在"})


@app.route("/set_new_stock", methods=['post'])
def set_new_stock():
    """
    保存当天新股数据
    """
    if request.method == "POST":
        data = request.form.to_dict()
        cache_date = convert_date_to_date_int(datetime.datetime.now())
        if data:
            if data['ipo_date'] == str(cache_date):
                # 存内存
                if str(cache_date) not in cache_data['东方财富']['新股'].keys() or str(cache_date) not in cache_data['同花顺']['新股']:
                    cache_data['东方财富']['新股'][str(cache_date)] = {}
                    cache_data['同花顺']['新股'][str(cache_date)] = {}
                # 删除其他天数得缓存数据
                for i in list(cache_data['东方财富']['新股'].keys()):
                    if i != str(cache_date):
                        del cache_data['东方财富']['新股'][i]
                for j in list(cache_data['同花顺']['新股'].keys()):
                    if j != str(cache_date):
                        del cache_data['同花顺']['新股'][j]
                if str(data.get('platform')) == str(1):
                    cache_data['东方财富']['新股'][str(cache_date)][data['code']] = data
                else:
                    cache_data['同花顺']['新股'][str(cache_date)][data['code']] = data
                # 存数据
                sql = "INSERT INTO new_stock(code, sub_code, name, ipo_date, issue_date,\
                                     amount,market_amount,price,pe,limit_amount,funds,ballot,create_time,platform) " \
                            "VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}','{}')".format(
                            data['code'], data['sub_code'], data['name'], data['ipo_date'], data['issue_date'], data['amount'],
                            data['market_amount'], data['price'], data['pe'], data['limit_amount'],
                            data['funds'], data['ballot'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),data['platform'])
                db.execute_db(sql)
                return jsonify({"code": 0, "msg": "保存成功"})
            else:
                return jsonify({"code": 1, "msg": "不是今日数据"})
        else:
            return jsonify({"code": 1, "msg": "数据为空"})
    else:
        return jsonify({"code": 1, "msg": "数据格式错误"})


@app.route("/set_new_bond", methods=['post'])
def set_new_bond():
    """
    保存当天新债数据
    """
    if request.method == "POST":
        data = request.form.to_dict()
        cache_date = convert_date_to_date_int(datetime.datetime.now())
        if data:
            if data['date'] == str(cache_date):
                # 存内存
                if str(cache_date) not in cache_data['东方财富']['新债'].keys() or str(cache_date) not in cache_data['同花顺']['新债']:
                    cache_data['东方财富']['新债'][str(cache_date)] = {}
                    cache_data['同花顺']['新债'][str(cache_date)] = {}
                # 删除其他天数得缓存数据
                for i in list(cache_data['东方财富']['新债'].keys()):
                    if i != str(cache_date):
                        del cache_data['东方财富']['新债'][i]
                for j in list(cache_data['同花顺']['新债'].keys()):
                    if j != str(cache_date):
                        del cache_data['同花顺']['新债'][j]
                if str(data.get('platform')) == str(1):
                    cache_data['东方财富']['新债'][str(cache_date)][data['code']] = data
                else:
                    cache_data['同花顺']['新债'][str(cache_date)][data['correcode']] = data
                # 存数据库
                sql = "INSERT INTO new_bond(code, sub_code, correcode, name, correcode_name,date,\
                                     pricenew,transfer_price,create_time,platform) " \
                                "VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}','{}')".format(
                                data['code'], data['sub_code'], data['correcode'], data['name'], data['correcode_name'],
                                data['date'], data['pricenew'], data['transfer_price'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),data['platform'])

                db.execute_db(sql)
                return jsonify({"code": 0, "msg": "保存成功"})
            else:
                return jsonify({"code": 1, "msg": "不是今日数据"})
        else:
            return jsonify({"code": 1, "msg": "数据为空"})
    else:
        return jsonify({"code": 1, "msg": "数据格式错误"})


@app.route("/get_new_stock", methods=["GET"])
def get_new_stock():
    """获取今日新股"""
    time_int = convert_date_to_date_int(datetime.datetime.now())

    new_stock_list = []
    # 内存查询 东方财富为准
    if time_int in cache_data['东方财富']['新股'].keys():
        new_stock_list.append(cache_data['东方财富']['新股'][str(time_int)])
    # 没数据  数据库查询
    if new_stock_list == []:
        sql = "SELECT * FROM new_stock WHERE ipo_date = '{}' AND platform = 1".format(time_int)
        new_stock_list += db.select_db(sql)


    return jsonify({"code": 0, "data": new_stock_list, "msg": "查询成功"})


@app.route("/get_new_bond", methods=["GET"])
def get_new_bond():
    """获取今日新债"""
    time_int = convert_date_to_date_int(datetime.datetime.now())

    new_bond_list = []
    # 内存查询 东方财富为准
    if time_int in cache_data['东方财富']['新债'].keys():
        new_bond_list.append(cache_data['东方财富']['新债'][str(time_int)])
    # 没数据  数据库查询
    if new_bond_list == []:
        sql = "SELECT * FROM new_bond WHERE date = '{}' AND platform = 1".format(time_int)
        new_bond_list += db.select_db(sql)

    return jsonify({"code": 0, "data": new_bond_list, "msg": "查询成功"})


@app.route("/get_stock_limit", methods=["GET"])
def get_stock_limit():
    """获取行情"""
    date_int = convert_date_to_date_int(datetime.datetime.now())

    df_date = pro.trade_cal(exchange='', start_date=str(
        date_int), end_date=str(date_int), fields='cal_date,pretrade_date')
    pretrade_date = df_date['pretrade_date'].values[0]

    code = request.args.get("code")

    market_list = []

    if code:
        df = pro.daily(ts_code=code,
                       start_date=str(pretrade_date), end_date=str(pretrade_date))

        for market in df.iterrows():
            market_data = dict(market[1])
            # market_data['up_limit'] = new_round(
            #     market_data['pre_close']*1.1, 2)
            # market_data['down_limit'] = new_round(
            #     market_data['pre_close']*0.9, 2)

            res_data = {}
            res_data['code'] = code
            res_data['pre_close'] = market_data['close']
            res_data['up_limit'] = new_round(market_data['close']*1.1, 2)
            res_data['down_limit'] = new_round(market_data['close']*0.9, 2)

            market_list.append(res_data)

    return jsonify({"code": 0, "data": market_list, "msg": "查询成功"})



@app.route("/remove_cache_data", methods=["GET"])
def remove_cache_data():
    """
    清除缓存
    Returns
    -------

    """
    cache_data = {
        "东方财富":{
            "新股":{},
            "新债": {}
        },
        "同花顺":{
            "新股":{},
            "新债": {}
        }
    }
    return jsonify(cache_data)



@app.route("/info", methods=["GET"])
def get_info():
    """

    """
    logger.debug(cache_data)
    return jsonify(cache_data)


@app.route("/show", methods=["GET"])
def show():
    """
    展示数据
    """
    return render_template("stock.html",encoding='UTF-8')

@app.route("/get_all_data", methods=["GET"])
def get_all_data():
    """
    数据库新股
    Returns
    -------
    """
    data = request.args.get("data")
    result = []
    if data == "stock":
        sql = "select * from new_stock"
        result.append(db.select_db(sql))
        return jsonify({"code": 0, "data": result, "msg": "查询成功"})
    if data == "bond":
        sql = "select * from new_bond"
        result.append(db.select_db(sql))
        return jsonify({"code": 0, "data": result, "msg": "查询成功"})
    return jsonify({"code": 1, "data": result, "msg": "参数错误"})

@app.route("/delete_stock", methods=["GET"])
def delete_stock():
    """
    删除新股id
    Returns
    -------

    """
    id = request.args.get("id")
    types = request.args.get('type')
    logger.debug(id)
    logger.debug(types)
    return jsonify({'code':0,'msg':"删除成功"})

@app.route("/edit_stock", methods=["post"])
def edit_stock():
    """
    编辑新股信息
    Returns
    -------

    """
    form_data = request.form.to_dict()
    sql = "update new_stock set amount='{}',ballot='{}',code='{}',funds='{}',ipo_date='{}',issue_date='{}',limit_amount='{}',market_amount='{}',name='{}',pe='{}',price='{}',sub_code='{}' where id='{}'".format(
        form_data['amount'],form_data['ballot'],form_data['code'],form_data['funds'],form_data['ipo_date'],
        form_data['issue_date'], form_data['limit_amount'], form_data['market_amount'], form_data['name'],form_data['pe'],
        form_data['price'], form_data['sub_code'], form_data['id']
    )
    db.execute_db(sql)
    return jsonify({'code':0,'msg':"编辑成功"})

@app.route("/add_stock", methods=["post"])
def add_stock():
    """
    添加新股信息
    Returns
    -------

    """
    form_data = request.form.to_dict()
    logger.debug(form_data)
    sql = "insert into new_stock(code,sub_code,name,ipo_date,issue_date,amount,market_amount,price,pe,limit_amount,funds,ballot,platform) values ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
        form_data['code'], form_data['sub_code'], form_data['name'], form_data['ipo_date'], form_data['issue_date'],
        form_data['amount'], form_data['market_amount'], form_data['price'], form_data['pe'],
        form_data['limit_amount'],
        form_data['funds'], form_data['ballot'], form_data['platform']
    )
    db.execute_db(sql)
    return jsonify({'code':0,'msg':"添加成功"})

@app.route("/edit_bond", methods=["post"])
def edit_bond():
    """
    编辑新债信息
    Returns
    -------

    """
    form_data = request.form.to_dict()
    logger.debug(form_data)
    sql = "update new_bond set code='{}',sub_code='{}',correcode='{}',name='{}',correcode_name='{}',pricenew='{}',transfer_price='{}',platform='{}' where id='{}'".format(
        form_data['code'], form_data['sub_code'], form_data['correcode'], form_data['name'], form_data['correcode_name'],
        form_data['pricenew'], form_data['transfer_price'], form_data['platform'],
        form_data['id']
    )
    db.execute_db(sql)
    return jsonify({'code':0,'msg':"编辑成功"})


@app.route("/add_bond", methods=["post"])
def add_bond():
    """
    添加新股信息
    Returns
    -------

    """
    form_data = request.form.to_dict()
    logger.debug(form_data)
    sql = "insert into new_bond(code,sub_code,correcode,name,correcode_name,date,pricenew,transfer_price,platform) values ('{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
        form_data['code'], form_data['sub_code'], form_data['correcode'], form_data['name'], form_data['correcode_name'],
        form_data['date'], form_data['pricenew'], form_data['transfer_price'], form_data['platform']
    )
    db.execute_db(sql)
    return jsonify({'code':0,'msg':"添加成功"})