from datetime import datetime
from selenium.webdriver import Keys


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def check_generator_is_empty(gen):
    is_empty = True
    for _ in gen:
        is_empty = False
        break
    return is_empty


def check_element_text_is_empty(element):
    is_empty = False
    try:
        if element.text.strip() == "" or ["MM", "YYYY"] in element.text or element.get_attribute("value") == "":
            is_empty = True
    except Exception as e:
        pass
    else:
        return is_empty


def convert_strdate_to_numbpad_keys(str_date):
    keys_list = []
    for element in str_date:
        try:
            number = int(element)
            if number == 0:
                keys_list.append(Keys.NUMPAD0)
            elif number == 1:
                keys_list.append(Keys.NUMPAD1)
            elif number == 2:
                keys_list.append(Keys.NUMPAD2)
            elif number == 3:
                keys_list.append(Keys.NUMPAD3)
            elif number == 4:
                keys_list.append(Keys.NUMPAD4)
            elif number == 5:
                keys_list.append(Keys.NUMPAD5)
            elif number == 6:
                keys_list.append(Keys.NUMPAD6)
            elif number == 7:
                keys_list.append(Keys.NUMPAD7)
            elif number == 8:
                keys_list.append(Keys.NUMPAD8)
            elif number == 9:
                keys_list.append(Keys.NUMPAD9)
        except ValueError:
            continue

    return keys_list


def today_date_in_keys():
    today_date = datetime.now().date()
    date_str = (str(today_date.month) +
                "/" +
                str(today_date.month) +
                "/" +
                str(today_date.day))
    return convert_strdate_to_numbpad_keys(date_str)
