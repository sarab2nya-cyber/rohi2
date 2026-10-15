import re
_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm(s):
    s = str(s).translate(_DIG).replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()
def to_num(v):
    s = norm(v).replace(",", "").replace("٬", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        x = float(s)
        return -x if neg else x
    except ValueError:
        return None
