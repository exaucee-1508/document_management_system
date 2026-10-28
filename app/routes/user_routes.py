from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

user_bp = Blueprint("users", __name__, url_prefix="/users")


@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data or not all(data.get(field) for field in
                           ["organization_id", "name", "email", "password"]):
        return jsonify({"error": "All fields are required"}), 400

    user = User(
        organization_id=data["organization_id"],
        name=data["name"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        role=data.get("role", "member")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "organization_id": user.organization_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 201

@user_bp.route("/", methods=["GET"])
def get_users():
    users = User.query.all()

    return jsonify([
        {
            "id": user.id,
            "organization_id": user.organization_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]), 200

@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "organization_id": user.organization_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 200

@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "name" in data:
        user.name = data["name"]

    if "email" in data:
        user.email = data["email"]

    if "role" in data:
        user.role = data["role"]

    db.session.commit()

    return jsonify({
        "id": user.id,
        "organization_id": user.organization_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 200

@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
    "message": "User deleted successfully"
    }), 200