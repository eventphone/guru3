import os

from django.conf import settings
from django.http import FileResponse, HttpResponse, Http404

from core.models import AudioFile
from core.tasks import process_ringback_file

from gcontrib.views.edit import OwnerSettingCrispyCreateView


class CreateRingbackView(OwnerSettingCrispyCreateView):
    def form_valid(self, form):
        result = super().form_valid(form)
        process_ringback_file.delay(form.instance.pk)
        return result


def download_audio(source_dir, request, hash):
    # Just check if this exists in principle
    if not AudioFile.objects.filter(sha512=hash).exists():
        raise Http404()

    outfile = os.path.join(source_dir, hash) + ".slin"
    # check if conversion ready
    if not os.path.isfile(outfile):
        return HttpResponse(b"Converted audio not available yet.", status=425)

    return FileResponse(open(outfile, "rb"))
