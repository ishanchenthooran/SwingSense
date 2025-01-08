import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from services.ai_feedback import generate_feedback

# Initializing Flask app
app = Flask(__name__, template_folder="views", static_folder="assets")

# Configuring SQLite database (using absolute path)
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'database', 'swingsense.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Defining database model
class SwingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    swing_issue = db.Column(db.String(255), nullable=False)
    feedback = db.Column(db.Text, nullable=False)

# Creating database tables
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    swing_issue = data.get("swing_issue")
    feedback = generate_feedback(swing_issue)

    # Saving to the database
    new_log = SwingLog(swing_issue=swing_issue, feedback=feedback)
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"feedback": feedback})

@app.route("/logs", methods=["GET"])
def logs():
    # Retrieving all logs from the database
    logs = SwingLog.query.all()
    return jsonify([{"id": log.id, "swing_issue": log.swing_issue, "feedback": log.feedback} for log in logs])

if __name__ == "__main__":
    app.run(debug=True)
