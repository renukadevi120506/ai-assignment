from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.models.submission import Document
from app.services.document_service import DocumentService
from app.utils.helpers import allowed_file, teacher_required

document_bp = Blueprint("document", __name__, url_prefix="/documents")

@document_bp.route("/")
@document_bp.route("/list")
@login_required
@teacher_required
def list_documents():
    docs = Document.query.filter_by(teacher_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template("teacher/documents.html", documents=docs)

@document_bp.route("/upload", methods=["GET", "POST"])
@login_required
@teacher_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected.", "warning")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                doc_record = DocumentService.process_and_save_document(
                    teacher_id=current_user.id,
                    uploaded_file=file,
                    upload_folder=upload_folder
                )
                flash(f"Document '{doc_record.original_filename}' uploaded and indexed into {doc_record.chunk_count} semantic chunks!", "success")
                return redirect(url_for("document.list_documents"))
            except Exception as e:
                flash(f"Error processing document: {e!s}", "danger")
        else:
            flash("Invalid file format. Allowed formats: PDF, DOCX, TXT.", "danger")

    return render_template("teacher/upload_document.html")

@document_bp.route("/<string:id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete(id):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    success = DocumentService.delete_document(id, current_user.id, upload_folder)
    if success:
        flash("Document and its vector embeddings deleted successfully.", "info")
    else:
        flash("Document not found or unauthorized.", "danger")
    return redirect(url_for("document.list_documents"))
