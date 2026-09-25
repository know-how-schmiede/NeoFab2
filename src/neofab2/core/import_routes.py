"""Admin-only two-step import; source hashes never enter HTML or sessions."""
from flask import Blueprint, current_app, g, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from .auth import permission_required
from .user_import import MAX_BYTES, ImportFailure, preview, apply_import

bp = Blueprint('user_import', __name__)
REPORT_LABELS = {
    'create': 'Create', 'update': 'Update', 'unchanged': 'Unchanged', 'skip': 'Skip', 'conflict': 'Conflict',
    'source_deleted': 'Source account marked deleted', 'invalid_fields': 'Invalid account fields',
    'duplicate_email': 'Duplicate source email', 'missing_target': 'Target account missing',
    'email_collision': 'Email already in use', 'source_unchanged': 'Source unchanged; target retained',
    'local_changes': 'Conflicting local changes', 'unknown_option': 'Option missing or disabled',
    'reset_required': 'Disabled; new password and activation required', 'ready': 'Ready',
    'last_admin': 'Last active administrator protected',
}


@bp.route('/admin/users/import', methods=['GET', 'POST'])
@permission_required('core.users.manage')
def index():
    report = None
    error = None
    if request.method == 'POST':
        upload = request.files.get('file')
        try:
            if upload is None:
                raise ImportFailure('Choose an import file.')
            raw = upload.stream.read(MAX_BYTES + 1)
            action = request.form.get('action')
            if action == 'preview':
                report = preview(current_app, raw, actor_id=g.current_user['id'])
            elif action == 'apply':
                if request.form.get('confirm') != 'yes':
                    raise ImportFailure('Confirm the import explicitly.')
                report = apply_import(current_app, raw, request.form.get('plan'), actor_id=g.current_user['id'])
            else:
                raise ImportFailure('Invalid import action.')
        except ImportFailure as failure:
            error = str(failure)
        except SQLAlchemyError:
            # Never expose SQL parameters/password hashes in a traceback or response.
            error = 'Import database operation failed. No accounts were changed.'
    return render_template('user_import.html', report=report, error=error, labels=REPORT_LABELS), 400 if error else 200
