import os, sys
from config.setting import SERVER_PORT
# from api.data_api import app
from api.test_api import app
# from flask_apidoc.commands import GenerateApiDoc
# from flask_script import Manager

# manager = Manager(app)
# manager.add_command('apidoc', GenerateApiDoc())

if __name__ == '__main__':
    # host为主机ip地址，port指定访问端口号，debug=True设置调试模式打开
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=True)
    # manager.run()
