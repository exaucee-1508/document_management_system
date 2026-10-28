from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.document import Document
import os
import uuid
from werkzeug.utils import secure_filename

document_bp = Blueprint(
    "documents", __name__, url_prefix="/documents"
)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "png", "jpg", "jpeg"}


@document_bp.route("/upload", methods=["POST"])
def upload_document():
    file = request.files.get("file")
    organization_id = request.form.get("organization_id", type=int)
    uploaded_by = request.form.get("uploaded_by", type=int)

    if not file or not file.filename:
        return jsonify({"error": "A file is required"}), 400

    if not organization_id or not uploaded_by:
        return jsonify({"error": "Organization ID and user ID are required"}), 400

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
    "uploaded_at": document.uploaded_at.isoformat()
    }), 201