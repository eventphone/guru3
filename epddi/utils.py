import datetime

import names


def datetime_to_asn1time_string(datetime_):
    """
    Converts datetime.datetime object to UTCTime/GeneralizedTime string
    following RFC5280. (Returns string encoded in UTCtime for dates through year
    2049, otherwise in GeneralizedTime format)
    """
    generalized_time = '%Y%m%d%H%M%SZ'
    utc_time = '%y%m%d%H%M%SZ'
    if datetime_.year < 2050:
        return datetime_.strftime(utc_time).encode("ascii")
    return datetime_.strftime(generalized_time).encode("ascii")


def get_new_router_name():
    return names.get_full_name(gender='female').replace(" ", "")