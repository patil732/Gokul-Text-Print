import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection
from utils.logger import logger

auth_bp = Blueprint('auth', __name__)

# Normalize role strings to standard 2-role RBAC: "Admin", "CEO"
ROLE_MAP = {
    "admin": "Admin",
    "Admin": "Admin",
    "ceo": "CEO",
    "CEO": "CEO",
    "ceo admin": "CEO",
    "CEO Admin": "CEO",
    "ceo_admin": "CEO",
}


@auth_bp.route('/register', methods=['GET', 'POST'])
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    if request.method == 'POST':
        is_api = request.is_json or request.path.startswith('/api/auth')
        if request.is_json:
            data = request.get_json(silent=True) or {}
            username = (data.get('username') or '').strip()
            password = data.get('password') or ''
            role = data.get('role', 'CEO')
            email = (data.get('email') or '').strip()
            company = (data.get('company') or '').strip()
        else:
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            role = request.form.get('role', 'CEO')
            email = (request.form.get('email') or '').strip()
            company = (request.form.get('company') or '').strip()

        if not username or not password:
            if is_api:
                return jsonify({"success": False, "error": "Username and password are required"}), 400
            flash('Username and password required', 'danger')
            return render_template('register.html')

        if len(password) < 8:
            if is_api:
                return jsonify({"success": False, "error": "Password must be at least 8 characters long for enterprise security."}), 400
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('register.html')

        if email and ('@' not in email or '.' not in email):
            if is_api:
                return jsonify({"success": False, "error": "Please provide a valid work email address."}), 400
            flash('Please provide a valid work email address.', 'danger')
            return render_template('register.html')

        role_norm = ROLE_MAP.get(str(role).strip(), ROLE_MAP.get(str(role).strip().lower(), "CEO"))

        conn = get_db_connection()
        # Check if username or email already exists
        existing = conn.execute(
            'SELECT username FROM users WHERE username = ? OR (email != "" AND email = ?)',
            (username, email)
        ).fetchone()

        if existing:
            conn.close()
            if is_api:
                return jsonify({"success": False, "error": "An account with this username or email already exists."}), 409
            flash('An account with this username or email already exists.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        try:
            conn.execute(
                'INSERT INTO users (username, password, role, email, company) VALUES (?, ?, ?, ?, ?)',
                (username, hashed_password, role_norm, email, company)
            )
            conn.commit()
            conn.close()

            if is_api:
                return jsonify({
                    "success": True,
                    "message": "Enterprise account registered successfully! You may now sign in.",
                    "user": {
                        "username": username,
                        "role": role_norm,
                        "email": email,
                        "company": company,
                    }
                }), 201

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            conn.close()
            if is_api:
                return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500
            flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    if request.method == 'POST':
        is_api = request.is_json or request.path.startswith('/api/auth')
        if request.is_json:
            data = request.get_json(silent=True) or {}
            username = data.get('username') or data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            if is_api:
                return jsonify({"success": False, "error": "Username and password are required"}), 400
            flash('Please provide both username and password.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            role_norm = ROLE_MAP.get(user['role'], user['role'])
            session['user'] = user['username']
            session['role'] = role_norm

            user_data = {
                "id": user['id'],
                "username": user['username'],
                "role": role_norm,
                "email": user['email'] if 'email' in user.keys() and user['email'] else f"{user['username']}@gokultextprint.internal",
            }

            if is_api:
                return jsonify({
                    "success": True,
                    "message": "Login successful",
                    "user": user_data,
                })

            if role_norm.lower() == 'ceo':
                return redirect(url_for('ceo.ceo_view'))
            else:
                return redirect(url_for('admin.admin_view'))
        else:
            if is_api:
                return jsonify({"success": False, "error": "Invalid username or password."}), 401
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
@auth_bp.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    is_api = request.is_json or request.path.startswith('/api/auth')
    if is_api:
        return jsonify({"success": True, "message": "Successfully logged out."})
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """
    Returns the authenticated user details from the active session.
    """
    if 'user' not in session:
        return jsonify({"authenticated": False, "user": None}), 401

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['user'],)).fetchone()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None}), 401

    role_norm = ROLE_MAP.get(user['role'], user['role'])
    # Ensure session matches normalized role
    session['role'] = role_norm

    return jsonify({
        "authenticated": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": role_norm,
            "email": user['email'] if 'email' in user.keys() and user['email'] else f"{user['username']}@gokultextprint.internal",
        }
    })


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Generates a secure password reset token valid for 1 hour.
    """
    data = request.get_json(silent=True) or {}
    identifier = data.get('username') or data.get('email') or ''
    identifier = identifier.strip()

    if not identifier:
        return jsonify({"success": False, "error": "Username or email is required."}), 400

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?',
        (identifier, identifier)
    ).fetchone()

    if not user:
        conn.close()
        # For security, return generic message but omit token
        return jsonify({
            "success": True,
            "message": "If that account exists in the mill database, password reset instructions have been generated.",
        })

    # Generate token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        'INSERT INTO password_reset_tokens (username, token, expires_at) VALUES (?, ?, ?)',
        (user['username'], token, expires_at)
    )
    conn.commit()
    conn.close()

    logger.info(f"[auth] Password reset token generated for user '{user['username']}'")

    return jsonify({
        "success": True,
        "message": f"Password reset instructions generated for '{user['username']}'.",
        "reset_token": token,
        "reset_url": f"/reset-password?token={token}",
        "expires_in": "1 hour",
    })


@auth_bp.route('/api/auth/verify-reset-token', methods=['GET'])
def verify_reset_token():
    """
    Validates if a reset token is valid, unexpired, and unused.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({"valid": False, "error": "Token is required."}), 400

    conn = get_db_connection()
    record = conn.execute(
        'SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0',
        (token,)
    ).fetchone()
    conn.close()

    if not record:
        return jsonify({"valid": False, "error": "Invalid or expired reset token."}), 404

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if record['expires_at'] < now_str:
        return jsonify({"valid": False, "error": "Reset token has expired."}), 400

    return jsonify({
        "valid": True,
        "username": record['username'],
    })


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Resets the user's password using a verified token.
    """
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({"success": False, "error": "Token and new password are required."}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters long."}), 400

    conn = get_db_connection()
    record = conn.execute(
        'SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0',
        (token,)
    ).fetchone()

    if not record:
        conn.close()
        return jsonify({"success": False, "error": "Invalid or expired reset token."}), 404

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if record['expires_at'] < now_str:
        conn.close()
        return jsonify({"success": False, "error": "Reset token has expired. Please request a new link."}), 400

    username = record['username']
    hashed_password = generate_password_hash(new_password)

    conn.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
    conn.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
    conn.commit()
    conn.close()

    logger.info(f"[auth] Password successfully reset for user '{username}'")

    return jsonify({
        "success": True,
        "message": "Password successfully updated! You may now sign in with your new credentials.",
    })


@auth_bp.route('/api/auth/profile', methods=['PUT', 'POST'])
def update_profile():
    """
    Updates the profile for the currently logged-in user.
    """
    if 'user' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['user'],)).fetchone()

    if not user:
        conn.close()
        session.clear()
        return jsonify({"success": False, "error": "User not found"}), 404

    if email is not None:
        conn.execute('UPDATE users SET email = ? WHERE id = ?', (email, user['id']))

    if password:
        if len(password) < 6:
            conn.close()
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        hashed = generate_password_hash(password)
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user['id']))

    conn.commit()
    updated_user = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
    conn.close()

    role_norm = ROLE_MAP.get(updated_user['role'], updated_user['role'])
    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "user": {
            "id": updated_user['id'],
            "username": updated_user['username'],
            "role": role_norm,
            "email": updated_user['email'] if 'email' in updated_user.keys() and updated_user['email'] else f"{updated_user['username']}@gokultextprint.internal",
        }
    })
