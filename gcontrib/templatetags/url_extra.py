from django import template
from django.http import QueryDict

register = template.Library()


@register.tag(name="url_parameters")
def parse_url_parameters(parser, token):
    parameters = token.split_contents()
    params = []
    for param in parameters[1:]:  # first is the tagname itself, we dont want this
        subTokens = param.split("=")
        if len(subTokens) == 1:
            params.append(template.Variable(subTokens[0]))
        elif len(subTokens) == 2:
            name = subTokens[0]
            value = subTokens[1]
            if value[0] == value[-1] and value[0] in ("'", '"'):
                # this is an absolute value
                params.append((name, value[1:-1]))
            else:
                # we assume that this is a variable to be resolved
                params.append((name, template.Variable(value)))
        else:
            raise template.TemplateSyntaxError(
                "{} accepts two types of parameters: variable names of dictionaries or name=data kind of assignments. You provided :\"{}\"".format(
                    parameters[0], param))

    return UrlParametersNode(params)


class UrlParametersNode(template.Node):
    def __init__(self, params):
        self.params = params

    @staticmethod
    def lookup(variable, context, default=""):
        try:
            return variable.resolve(context)
        except template.VariableDoesNotExist:
            return default

    def render(self, context):
        d = {}
        for param in self.params:
            if isinstance(param, tuple):
                name, value = param
                if isinstance(value, template.Variable):
                    d[name] = UrlParametersNode.lookup(value, context)
                else:
                    d[name] = value
            else:
                data = UrlParametersNode.lookup(param, context, {})
                if not isinstance(data, dict):
                    data = {}
                d.update(data)

        qd = QueryDict(mutable=True)
        qd.update(d)
        return qd.urlencode()
