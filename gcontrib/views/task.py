from csv import writer

from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View


class JobProcessingView(TemplateResponseMixin, ContextMixin, View):
    job_function = None

    def __init__(self, *args, **kwargs):
        self.context_data = {}
        super(JobProcessingView, self).__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.job_function(request, self, *args, **kwargs)

    def add_context(self, key, data):
        self.context_data[key] = data

    def redirect_to(self, url):
        return HttpResponseRedirect(url)

    def render_template(self):
        context = self.get_context_data(**self.context_data)
        return self.render_to_response(context)


class CSVExportView(View):
    http_method_names = ["get"]

    # A function that takes the request and kwargs and should return a tuple that contains
    # a header list and a list of rows for CSV export
    csv_function = None

    filename = None

    def get(self, request, *args, **kwargs):
        (header, data) = self.csv_function(request, kwargs)

        if callable(self.filename):
            filename = self.filename(request, kwargs)
        else:
            filename = self.filename

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=\"{}\"".format(filename)
        w = writer(resp)
        w.writerow(header)
        for row in data:
            w.writerow(row)
        return resp
