from app import create_app
from flask_sqlalchemy import SQLAlchemy

app = create_app()
app.config.from_object('config.Config')  # load from config.py
db = SQLAlchemy(app)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
