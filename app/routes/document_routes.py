from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.document import Document
import os
import uuid
from werkzeug.utils import secure_filename
from app.models.organization import Organization
from app.models.user import User
from flask import Blueprint, request, jsonify, current_app, send_file


document_bp = Blueprint(
    "documents", __name__, url_prefix="/documents"
)

ALLOWED_EXTENSIONS = {"pdf", "txt", "png", "jpg", "jpeg", "zip"}


@document_bp.route("/upload", methods=["POST"])
def upload_document():
    file = request.files.get("file")
    organization_id = request.form.get("organization_id", type=int)
    uploaded_by = request.form.get("uploaded_by", type=int)

    if not file or not file.filename:
        return jsonify({"error": "A file is required"}), 400

    if not organization_id or not uploaded_by:
        return jsonify({"error": "Organization ID and user ID are required"}), 400

    organization = Organization.query.get(organization_id)
    if not organization:
        return jsonify({"error": "Organization not found"}), 404

    user = User.query.get(uploaded_by)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.organization_id != organization_id:
        return jsonify({
            "error": "This user does not belong to the specified organization"
        }), 403

    original_name = secure_filename(file.filename)

    if "." not in original_name:
        return jsonify({"error": "Invalid filename"}), 400

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File type not allowed"}), 400

    duplicate = Document.query.filter_by(
        organization_id=organization_id,
        name=original_name
    ).first()

    if duplicate:
        return jsonify({
            "error": "A document with this filename already exists. Rename the file and try again."
        }), 409

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    saved_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(upload_folder, saved_name)

    try:
        file.save(file_path)

        document = Document(
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            name=original_name,
            file_path=file_path,
            mime_type=file.mimetype or "application/octet-stream"
        )

        db.session.add(document)
        db.session.commit()

    except Exception:
        db.session.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        raise

    return jsonify({
    "id": document.id,
    "name": document.name,
    "organization_id": document.organization_id,
    "uploaded_by": document.uploaded_by,
    "mime_type": document.mime_type,
    "uploaded_at": document.uploaded_at.isoformat(),
    "message": "File uploaded successfully"
    }), 201

@document_bp.route("/", methods=["GET"])
def get_documents():
    documents = Document.query.all()

    return jsonify([
        {
            "id": doc.id,
            "organization_id": doc.organization_id,
            "uploaded_by": doc.uploaded_by,
            "name": doc.name,
            "mime_type": doc.mime_type,
            "uploaded_at": doc.uploaded_at.isoformat()
        }
        for doc in documents
    ]), 200

@document_bp.route("/<int:document_id>", methods=["GET"])
def get_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    return jsonify({
        "id": document.id,
        "organization_id": document.organization_id,
        "uploaded_by": document.uploaded_by,
        "name": document.name,
        "mime_type": document.mime_type,
        "uploaded_at": document.uploaded_at.isoformat()
    }), 200

@document_bp.route("/search", methods=["GET"])
def search_documents():
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({"error": "Please provide a filename to search"}), 400

    documents = Document.query.filter(
        Document.name.ilike(f"%{name}%")
    ).all()

    return jsonify([
        {
            "id": doc.id,
            "organization_id": doc.organization_id,
            "uploaded_by": doc.uploaded_by,
            "name": doc.name,
            "mime_type": doc.mime_type,
            "uploaded_at": doc.uploaded_at.isoformat()
        }
        for doc in documents
    ]), 200

@document_bp.route("/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    file_path = document.file_path

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()

    return jsonify({
        "message": "Document deleted successfully"
    }), 200

@document_bp.route("/<int:document_id>/download", methods=["GET"])
def download_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    if not os.path.exists(document.file_path):
        return jsonify({"error": "Document file not found"}), 404

    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.name,
        mimetype=document.mime_type
    )

@document_bp.route("/<int:document_id>/replace", methods=["PUT"])
def replace_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    file = request.files.get("file")

    if not file or not file.filename:
        return jsonify({"error": "A replacement file is required"}), 400

    original_name = secure_filename(file.filename)

    if "." not in original_name:
        return jsonify({"error": "Invalid filename"}), 400

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File type not allowed"}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    saved_name = f"{uuid.uuid4().hex}_{original_name}"
    new_file_path = os.path.join(upload_folder, saved_name)

    try:
        file.save(new_file_path)

        old_file_path = document.file_path

        document.name = original_name
        document.file_path = new_file_path
        document.mime_type = file.mimetype or "application/octet-stream"

        db.session.commit()

        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    except Exception:
        db.session.rollback()

        if os.path.exists(new_file_path):
            os.remove(new_file_path)

        raise

    return jsonify({
        "message": "Document replaced successfully",
        "id": document.id,
        "name": document.name,
        "mime_type": document.mime_type
    }), 200

@document_bp.route("/<int:document_id>/view", methods=["GET"])
def view_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    if not os.path.exists(document.file_path):
        return jsonify({"error": "Document file not found"}), 404

    return send_file(
        document.file_path,
        as_attachment=False,
        mimetype=document.mime_type
    )