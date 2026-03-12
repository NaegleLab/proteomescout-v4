from flask import render_template, redirect, flash, url_for, request
from flask_login import login_required, logout_user, current_user, login_user
from app.utils.email import send_password_reset_email

import sqlalchemy as sa
from app.database.user import User, load_user_by_username, load_user_by_email#, send_password_reset_email
from app.auth.forms import LoginForm, SignupForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth import bp
from app import db


@bp.route('/login', methods=['GET', 'POST'])
def login():
    message = request.args.get('message')
    if message:
        flash(message)
    if current_user.is_authenticated:
        return redirect(url_for('info.home'))
    login_form = LoginForm(request.form)

    if request.method == 'POST':
        if login_form.validate():
            # Get Form Fields
            username = request.form.get('username')
            password = request.form.get('password')
            # Validate Login Attempt
            user = load_user_by_username(username)
            if user:
                if user.check_password(password=password):
                    login_user(user)
                    next = request.args.get('next')
                    return redirect(next or url_for('info.home'))
        flash('Invalid username/password combination')
        return redirect(url_for('auth.login'))
    # GET: Serve Log-in page
    return render_template('proteomescout/auth/login.html',
                           form=LoginForm()
                           )




@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User sign-up page."""
    signup_form = SignupForm(request.form)
    # POST: Sign user in
    if request.method == 'POST':
        if signup_form.validate():
            # Get Form Fields
            username = request.form.get('username')
            
            password = request.form.get('password')
            name = request.form.get('name')
            email = request.form.get('email')

            institution = request.form.get('institution')
            existing_username = load_user_by_username(username)
            existing_email = load_user_by_email(email)
            if existing_username is None and existing_email is None:
                user = User(username=username,
                            name=name,
                            email=email,
                            institution=institution
                            )
                user.create_user(password)
                user.process_invitations()
                
                db.session.add(user)
                db.session.commit()
                login_user(user)
                
                return redirect(url_for('info.home'))
            if existing_email is not None:
                flash('A user already exists with that email address.')
            if existing_username is not None:
                flash('A user already exists with that username.')
            return redirect(url_for('auth.signup'))
        flash('Invalid sign-up')
        
    # GET: Serve Sign-up page
    return render_template('/proteomescout/auth/signup.html',
                           title='Create an Account',
                           form=signup_form,
                           template='signup-page',
                           body="Sign up for a user account.")


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('/proteomescout/auth/reset_password_request.html',
                           title='Reset Password', form=form)
    #if form.validate_on_submit():
     #   user = db.session.scalar(
     ##       sa.select(User).where(User.email == form.email.data))
     #   if user:
     #       send_password_reset_email(user)
    #    flash('Check your email for the instructions to reset your password')
      #  return redirect(url_for('login'))
    #return render_template('/proteomescout/auth/reset_password_request.html',
          #                 title='Reset Password', form=form)

@bp.route('/auth/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('/proteomescout/auth/reset_password.html', form=form)