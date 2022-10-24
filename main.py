import os
import json
import oauthlib
import gspread
import datetime

from flask import (
    Flask,
    render_template,
    request, redirect, url_for, session, current_app, flash
)

from flask_dance.contrib.google import make_google_blueprint, google

from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError, TokenExpiredError
from dotenv import load_dotenv
from scripts import forms, gsmod
# from gspread.exceptions import APIError, GSpreadException

from scripts.gsmod import short_date_to_long as short_to_long, check_duplicate_booking, check_date, book_whole_day, book_half_day, location_to_str

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()


def _empty_session():
    """
    Deletes the google token and clears the session
    """
    if "google" in current_app.blueprints and hasattr(
            current_app.blueprints["google"], "token"
    ):
        del current_app.blueprints["google"].token
    session.clear()


app = Flask(__name__)
app.config["SECRET_KEY"] = "123456789asdfghjkl#A"

back_home = os.environ.get("BACK_HOME")
google_bp = make_google_blueprint(
    client_id=os.getenv("GOO_CLIENT"),
    client_secret=os.getenv("GOO_SHH"),
    scope=[
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="landing_page",
)

app.register_blueprint(google_bp, url_prefix="/login")


@app.errorhandler(oauthlib.oauth2.rfc6749.errors.TokenExpiredError)
@app.errorhandler(oauthlib.oauth2.rfc6749.errors.InvalidClientIdError)
def token_expired(_):
    _empty_session()
    return redirect(url_for("landing_page"))


# TOKEN ERROR HANDLING #
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        error_message_title="Ooops...that's a 404 HTML code",
        error_message="The resource or page you are looking for has not been created yet. Click the button below to go back to the homescreen",
        error_message_url_for=url_for("landing_page"),
        error_button_label="Back to homescreen",
        error_button_link_target="",
    )


@app.errorhandler(500)
def template_not_found(e):
    print("error 500")


@app.route('/', methods=["GET", "POST"])
def landing_page():
    if not google.authorized:
        return redirect(url_for("google.login"))

    form = forms.FormBookDesk(request.form)
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text

    booking_data = {
        "email": resp.json()["email"],
        "date": form.booking_date.data,
        "time": form.booking_time.data,
        "name": resp.json()["name"],
        "picture": resp.json()["picture"]
    }

    if form.validate_on_submit():
        print(booking_data["email"] + "/" + str(booking_data["date"]) + "/" + booking_data["time"])

        # gsheet ops
        google_credentials = os.environ["GOO_CREDS"]
        ledger_gs = os.environ["LEDGERV2_ID"]
        credentials_dict = json.loads(google_credentials, strict=False)
        gc = gspread.service_account_from_dict(credentials_dict)

        # Open bookings sheetq
        wks_ledger = gc.open_by_key(ledger_gs).sheet1
        print("...sheet opened")

        staff = booking_data["email"]
        reservation_date = datetime.date.strftime(booking_data["date"], "%m/%d/%y")
        time_of_day = booking_data["time"]

        # staff = "r.c.delfin.org"
        # reservation_date = "10/24/22"
        # time_of_day = "AMPM"

        long_reservation_date = short_to_long(reservation_date)

        if check_duplicate_booking(wks_ledger=wks_ledger, requester=staff, request_date=reservation_date, request_time_of_day=time_of_day):
            flash(f"ERROR: Duplicate booking found for your requested reservation on {long_reservation_date} ({time_of_day})")
        else:
            if check_date(wks_ledger=wks_ledger, request_date=reservation_date):
                if time_of_day == "AMPM":
                    location_set = book_whole_day(wks_ledger=wks_ledger, requester=staff, request_date=reservation_date)
                else:
                    location_set = book_half_day(wks_ledger=wks_ledger, requester=staff, request_date=reservation_date,
                                                 request_time_of_day=time_of_day)
                if location_set:
                    # successful booking
                    flash(
                        f"Success! Booked you a desk for {long_reservation_date}, {location_to_str(loc_set=location_set, request_time_of_day=time_of_day)}")
                else:
                    flash(f"ERROR: Sorry, no more desks available for {long_reservation_date} ({time_of_day})")
            else:
                flash(
                    f"ERROR: Your requested date {long_reservation_date} is not a valid booking date - acceptable dates are from today to two (2) days ahead only")
    return render_template(
        'index.html',
        name=booking_data["name"],
        email=booking_data["email"],
        picture=booking_data["picture"],
        gohome=back_home,
        form=form
    )


if __name__ == '__main__':
    app.run()
