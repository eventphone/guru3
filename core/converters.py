from random import choice
from django.urls.resolvers import RoutePattern, URLResolver, URLPattern


class LegacyHostingConverter(object):
    extensions = ('php', 'cgi', 'exe', 'tcl', 'so', 'dll', 'sh', 'sql', 'py', 'aspx',
                  'pl', 'jsp', 'jsf', 'asm', 'bat', 'js', 'swf', 'ps1', 'vba', 'htaccess',
                  'reg', 'out', 'cmd', 'asp', 'wasm', 'rb', 'erb', 'lsp', 'do')
    regex = '(' + '|'.join(extensions) + ')'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return choice(self.extensions)


class LegacyRoutePattern(RoutePattern):

    def match(self, path):
        match = super().match(path)
        if match:
            (path, args, kwargs) = match
            for key, converter in self.converters.items():
                if (isinstance(converter, LegacyHostingConverter)):
                    del kwargs[key]
            return path, args, kwargs
        return None


def legacyPath(route, view, kwargs=None, name=None):
    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        pattern = LegacyRoutePattern(route, is_endpoint=False)
        urlconf_module, app_name, namespace = view
        return URLResolver(
            pattern,
            urlconf_module,
            kwargs,
            app_name=app_name,
            namespace=namespace,
        )
    elif callable(view):
        pattern = LegacyRoutePattern(route, name=name, is_endpoint=True)
        return URLPattern(pattern, view, kwargs, name)
    else:
        raise TypeError('view must be a callable or a list/tuple in the case of include().')
