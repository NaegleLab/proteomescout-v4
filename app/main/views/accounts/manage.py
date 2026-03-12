from app.main.views.accounts import bp
from flask import render_template, redirect, url_for, request
from flask_login import current_user
from app.config import strings
from app.main.forms.change_password_form import ChangePasswordForm

@bp.route('/', methods=['GET', 'POST'])
def manage():
    if current_user.is_authenticated:
        user = current_user

        form = ChangePasswordForm(current_user)

        if form.validate_on_submit():

            return redirect(url_for('info.home'))

        # if request.method == 'GET':
        #     print("GET")

        return render_template(
            'proteomescout/accounts/manage.html',
            title = strings.account_management_page_title,
            username = user.username,
            fullname = user.name,
            email = user.email,
            institution = user.institution,
            form = form,
        )

    else:
        user = None

        return render_template(
            'proteomescout/accounts/manage.html'
        )

