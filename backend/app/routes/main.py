from flask import Blueprint, jsonify

main_bp = Blueprint("main", __name__)

@main_bp.route("/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})