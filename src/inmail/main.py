from src.inmail.personalized_email import run_personalised_email
from src.inmail.template_email import run_template_email


def run_selenium_automation(
    linkedin_email,
    linkedin_password,
    data,
    visible_mode,
    email_template=None,
    callback=None,
):
    if email_template is None:
        run_personalised_email(
            data=data,
            visible_mode=visible_mode,
            callback=callback,
        )
    else:
        run_template_email(
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            data=data,
            visible_mode=visible_mode,
            email_template=email_template,
            callback=callback,
        )
