import hashlib

import magic
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from core.models import AudioFile


class AudioFileForm(ModelForm):
    class Meta:
        model = AudioFile
        fields = [
            "name",
            "file",
        ]
        widgets = {
            "owner": autocomplete.ModelSelect2(url="user.autocomplete"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(AudioFileForm, self).__init__(*args, **kwargs)

    def get_form_helper(self):
        helper = FormHelper()
        helper.add_input(Submit("save", _("Add Audio File")))
        return helper

    def clean_file(self):
        file_count = AudioFile.objects.filter(owner=self.user).count()
        if file_count > 5 and not self.user.is_staff:
            raise ValidationError(_('User quota exceeded. Delete files first. 5 files maximum.'), code='maxfiles')
        file = self.cleaned_data.get('file', False)
        if file.size > (5*1024*1024):
            raise ValidationError(_('Audio File is to large (>5MB)'), code='toolarge')
        buf = file.read()
        mime = magic.from_buffer(buf, mime=True)
        if mime not in ['audio/mpeg', 'audio/x-wav']:
            raise ValidationError(_('File format [%s] is wrong. Only MP3 and WAV is supported.' % mime),
                                  code='wrongformat')
        hash_object = hashlib.sha512(buf)
        self.instance.sha512 = hash_object.hexdigest()
        return file
