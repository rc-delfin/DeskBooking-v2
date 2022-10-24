from gspread.exceptions import APIError, GSpreadException
from datetime import datetime, timedelta


def found_a_booking(wks: object, requester: str, request_date: str, request_time_of_day: str) -> bool:
    """
    Usage: validate request date against the booking gsheet
    If found_a_booking is True, request date is INVALID
    """
    try:
        if request_time_of_day == "AMPM":
            # Test with AM first
            cell = wks.find(requester + "-" + request_date + "-AM")
            if cell:
                result = True
            else:
                # Test with PM
                cell = wks.find(requester + "-" + request_date + "-PM")
                if cell:
                    result = True
                else:
                    # Test with AMPM
                    cell = wks.find(requester + "-" + request_date + "-AMPM")
                    if cell:
                        result = True
                    else:
                        result = False
        elif request_time_of_day == "AM":
            cell = wks.find(requester + "-" + request_date + "-AM")
            if cell:
                result = True
            else:
                # try whole day search
                cell = wks.find(requester + "-" + request_date + "-AMPM")
                if cell:
                    result = True
                else:
                    result = False
        else:
            # PM
            cell = wks.find(requester + "-" + request_date + "-PM")
            if cell:
                result = True
            else:
                # try whole day search
                cell = wks.find(requester + "-" + request_date + "-AMPM")
                if cell:
                    result = True
                else:
                    result = False
    except APIError:
        result = False
    except GSpreadException:
        result = False
    return result




def make_key(requester: str, request_date: str, request_time_of_day: str) -> str:
    return request_date + "-" + request_time_of_day + "-" + requester


def check_duplicate_booking(wks_ledger: object, requester: str, request_date: str, request_time_of_day: str) -> bool:
    """
    Check if the booking request has a duplicate in the Ledger V2 Googlesheet or not
    :param wks_ledger:
    :param requester:
    :param request_date:
    :param request_time_of_day:
    :return: True - a duplicate exists, otherwise False
    """
    try:
        if request_time_of_day == "AMPM":
            # Test with AM first
            cell = wks_ledger.find(make_key(requester, request_date, "AM"))
            if cell:
                result = True
            else:
                # Test with PM
                cell = wks_ledger.find(make_key(requester, request_date, "PM"))
                if cell:
                    result = True
                else:
                    # Test with AMPM
                    cell = wks_ledger.find(make_key(requester, request_date, "AMPM"))
                    if cell:
                        result = True
                    else:
                        result = False
        elif request_time_of_day == "AM":
            cell = wks_ledger.find(make_key(requester, request_date, "AM"))
            if cell:
                result = True
            else:
                # try whole day search
                cell = wks_ledger.find(make_key(requester, request_date, "AMPM"))
                if cell:
                    result = True
                else:
                    result = False
        else:
            # PM
            cell = wks_ledger.find(make_key(requester, request_date, "PM"))
            if cell:
                result = True
            else:
                # try whole day search
                cell = wks_ledger.find(make_key(requester, request_date, "AMPM"))
                if cell:
                    result = True
                else:
                    result = False
    except APIError or GSpreadException:
        result = False

    return result


def book_half_day(wks_ledger: object, requester: str, request_date: str, request_time_of_day: str) -> list:
    """
    Booking function applicable for AM or PM time of day only
    Search for a vacant desk, and if found, book the staff to that desk
    Otherwise, do nothing
    :param requester:
    :param request_date:
    :param request_time_of_day:
    :return: If a successful booking happened, return the location of the desk,
    otherwise return an empty list
    """
    cell = wks_ledger.find(make_key("vacant", request_date, request_time_of_day))
    if cell:
        print(cell)
        print(cell.row, cell.col)

        cell_list = wks_ledger.range(cell.row, cell.col - 1, cell.row, cell.col)
        cell_list[0].value = requester
        cell_list[1].value = make_key(requester, request_date, request_time_of_day)
        wks_ledger.update_cells(cell_list, value_input_option='RAW')
        location = wks_ledger.cell(cell.row, 1).value
        return [location]
    else:
        return []


def book_whole_day(wks_ledger: object, requester: str, request_date: str) -> list:
    """
    Booking function applicable for AMPM time of day only
    'All or nothing' approach - both AM and PM vacant desks should be found
    locations may be different between AM and PM bookings
    :param requester:
    :param request_date:
    :return: If booking is successful, return a list containing locations for AM and PM
    otherwise, return an empty list
    """
    cell_am = wks_ledger.find(make_key("vacant", request_date, "AM"))
    if cell_am:
        cell_pm = wks_ledger.find(make_key("vacant", request_date, "PM"))
        if cell_pm:
            cell_am_list = wks_ledger.range(cell_am.row, cell_am.col - 1, cell_am.row, cell_am.col)
            cell_am_list[0].value = requester
            cell_am_list[1].value = make_key(requester, request_date, "AM")

            cell_pm_list = wks_ledger.range(cell_pm.row, cell_pm.col - 1, cell_pm.row, cell_pm.col)
            cell_pm_list[0].value = requester
            cell_pm_list[1].value = make_key(requester, request_date, "PM")

            wks_ledger.update_cells(cell_am_list, value_input_option='RAW')
            wks_ledger.update_cells(cell_pm_list, value_input_option='RAW')
            location_am = wks_ledger.cell(cell_am.row, 1).value
            location_pm = wks_ledger.cell(cell_pm.row, 1).value
            result = [location_am, location_pm]
        else:
            result = []
    else:
        result = []
    return result


def check_date(wks_ledger: object, request_date: str) -> bool:
    """
    date validation - the requested date must exist in the ledger
    :param request_date:
    :return:
    """
    cell = wks_ledger.find(request_date)
    if cell:
        return True
    else:
        return False


def location_to_str(loc_set: list, request_time_of_day: str) -> str:
    if len(loc_set) > 1:
        if loc_set[0] == loc_set[1]:
            return loc_set[0] + " whole day"
        else:
            return loc_set[0] + " (AM), " + loc_set[1] + " (PM)"
    else:
        return loc_set[0] + " (" + request_time_of_day + ")"

def short_date_to_long(short_date: str) -> str:
    """
    convert mm/dd/yy to long format (e.g. Mon, 21 Sep 2022)
    :param short_date:
    :return:
    """
    date_obj = datetime.strptime(short_date, '%m/%d/%y')
    return datetime.strftime(date_obj, '%a, %d %b %Y')
