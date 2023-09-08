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
