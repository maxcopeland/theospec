from app import app
from threading import Thread
# from app.routes import bk_worker

# Thread(target=bk_worker).start()

if __name__ == "__main__":
    app.run(port=8000, debug=True)