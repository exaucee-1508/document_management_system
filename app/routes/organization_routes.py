from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.organization import Organization

organization_bp = Blueprint(
    "organizations", __name__, url_prefix="/organizations"
)


@organization_bp.route("/", methods=["POST"])
def create_organization():
    data = request.get_json()

    if not data or not data.get("name") or not data.get("email"):
        return jsonify({
            "error": "Name and email are required"
        }), 400

    organization = Organization(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(organization)
    db.session.commit()

    return jsonify({
        "id": organization.id,
        "name": organization.name,
        "email": organization.email,
        "created_at": organization.created_at.isoformat()
    }), 201

@organization_bp.route("/", methods=["GET"])
def get_organizations():
    organizations = Organization.query.all()

    return jsonify([
        {
            "id": org.id,
            "name": org.name,
            "email": org.email,
            "created_at": org.created_at.isoformat()
        }
        for org in organizations
    ]), 200

@organization_bp.route("/<int:org_id>", methods=["GET"])
def get_organization(org_id):
    organization = db.session.get(Organization, org_id)

    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    return jsonify({
        "id": organization.id,
        "name": organization.name,
        "email": organization.email,
        "created_at": organization.created_at.isoformat()
    }), 200

@organization_bp.route("/<int:org_id>", methods=["PUT"])
def update_organization(org_id):
    organization = db.session.get(Organization, org_id)

    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    data = request.get_json()

    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"error": "Name and email are required"}), 400

    organization.name = data["name"]
    organization.email = data["email"]

    db.session.commit()

    return jsonify({
        "id": organization.id,
        "name": organization.name,
        "email": organization.email
    }), 200

@organization_bp.route("/<int:org_id>", methods=["DELETE"])
def delete_organization(org_id):
    organization = db.session.get(Organization, org_id)

    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    db.session.delete(organization)
    db.session.commit()

    return jsonify({
        "message": "Organization deleted successfully"
    }), 200