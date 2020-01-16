import os
from LifeManager.WebServer import app


if __name__ == '__main__':
    app.root_path = os.getcwd()
    app.run()
