from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class ComplexPasswordValidator:
    """
    Validate whether the password contains minimum one uppercase, one digit and one symbol.
    """

    def validate(self, password, user=None):
        if None in [re.search('[A-Z]', password), re.search('[0-9]', password), re.search('[^A-Za-z0-9]', password)]:
            raise ValidationError(
                _("This password is not strong."),
                code='password_is_weak',
            )

    def get_help_text(self):
        return _(
            """
            At least 8 characters—the more characters, the better.
            A mixture of both uppercase and lowercase letters.
            A mixture of letters and numbers.
            Inclusion of at least one special character, e.g., ! @ # ? ]
            """
        )
