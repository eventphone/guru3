from django.contrib.auth.decorators import user_passes_test, login_required


def user_is_staff(func):
    return user_passes_test(lambda u: u.is_staff)(login_required(func))

def user_is_superuser(func):
    return user_passes_test(lambda u: u.is_superuser)(login_required(func))
