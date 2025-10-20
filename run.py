import os

from dotenv import load_dotenv
from app import create_app
# 加载 .env 文件中的环境变量
load_dotenv()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)