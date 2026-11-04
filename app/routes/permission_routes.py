from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.permission import Permission
from app.models.user import User
from app.models.document import Document

permission_bp = Blueprint(
    "permissions",
    __name__,
    url_prefix="/permissions"
)

@permission_bp.route("/", methods=["POST"])
def assign_permission():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    required_fields = ["user_id", "document_id", "admin_id"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "user_id, document_id, and admin_id are required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    document = Document.query.get(data["document_id"])
    if not document:
        return jsonify({"error": "Document not found"}), 404

    admin = User.query.get(data["admin_id"])
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    if admin.role != "admin":
        return jsonify({"error": "Only admins can assign permissions"}), 403

    if admin.organization_id != document.organization_id:
        return jsonify({
        "error": "You can only manage permissions for documents in your organization"
        }), 403

    if user.organization_id != document.organization_id:
        return jsonify({
        "error": "You can only assign permissions to users in your organization"
        }), 403

    existing_permission = Permission.query.filter_by(
        user_id=data["user_id"],
        document_id=data["document_id"]
    ).first()

    if existing_permission:
        return jsonify({"error": "Permission already exists"}), 409

    permission = Permission(
        user_id=data["user_id"],
        document_id=data["document_id"],
        can_view=data.get("can_view", False),
        can_download=data.get("can_download", False),
        can_edit=data.get("can_edit", False),
        can_delete=data.get("can_delete", False)
    )

    db.session.add(permission)
    db.session.commit()

    return jsonify({
        "id": permission.id,
        "user_id": permission.user_id,
        "document_id": permission.document_id,
        "can_view": permission.can_view,
        "can_download": permission.can_download,
        "can_edit": permission.can_edit,
        "can_delete": permission.can_delete,
        "message": "Permission created successfully"
    }), 201

@permission_bp.route("/", methods=["GET"])
def get_permissions():
    permissions = Permission.query.all()

    return jsonify([
        {
            "id": permission.id,
            "user_id": permission.user_id,
            "document_id": permission.document_id,
            "can_view": permission.can_view,
            "can_download": permission.can_download,
            "can_edit": permission.can_edit,
            "can_delete": permission.can_delete
        }
        for permission in permissions
    ]), 200

@permission_bp.route("/<int:permission_id>", methods=["GET"])
def get_permission(permission_id):
    permission = Permission.query.get(permission_id)

    if not permission:
        return jsonify({"error": "Permission not found"}), 404

    return jsonify({
        "id": permission.id,
        "user_id": permission.user_id,
        "document_id": permission.document_id,
        "can_view": permission.can_view,
        "can_download": permission.can_download,
        "can_edit": permission.can_edit,
        "can_delete": permission.can_delete
    }), 200

@permission_bp.route("/<int:permission_id>", methods=["PUT"])
def update_permission(permission_id):
    permission = Permission.query.get(permission_id)

    if not permission:
        return jsonify({"error": "Permission not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    admin_id = data.get("admin_id")
    if not admin_id:
        return jsonify({"error": "admin_id is required"}), 400

    admin = User.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    if admin.role != "admin":
        return jsonify({"error": "Only admins can update permissions"}), 403

    document = Document.query.get(permission.document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    if admin.organization_id != document.organization_id:
        return jsonify({
        "error": "You can only manage permissions for documents in your organization"
        }), 403

    permission.can_view = data.get("can_view", permission.can_view)
    permission.can_download = data.get("can_download", permission.can_download)
    permission.can_edit = data.get("can_edit", permission.can_edit)
    permission.can_delete = data.get("can_delete", permission.can_delete)

    db.session.commit()

    return jsonify({
        "message": "Permission updated successfully",
        "id": permission.id,
        "user_id": permission.user_id,
        "document_id": permission.document_id,
        "can_view": permission.can_view,
        "can_download": permission.can_download,
        "can_edit": permission.can_edit,
        "can_delete": permission.can_delete
    }), 200

@permission_bp.route("/<int:permission_id>", methods=["DELETE"])
def delete_permission(permission_id):
    permission = Permission.query.get(permission_id)

    if not permission:
        return jsonify({"error": "Permission not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    admin_id = data.get("admin_id")
    if not admin_id:
        return jsonify({"error": "admin_id is required"}), 400

    admin = User.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    if admin.role != "admin":
        return jsonify({"error": "Only admins can delete permissions"}), 403

    document = Document.query.get(permission.document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    if admin.organization_id != document.organization_id:
        return jsonify({
        "error": "You can only manage permissions for documents in your organization"
        }), 403

    db.session.delete(permission)
    db.session.commit()

    return jsonify({
        "message": "Permission deleted successfully"
    }), 200