from app import app
from app.simulator import simulator

if __name__ == "__main__":
    app.run(port=8000, debug=True)