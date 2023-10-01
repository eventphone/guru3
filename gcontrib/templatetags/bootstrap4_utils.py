from django import template

register = template.Library()


@register.tag(name="bootstrap4_form_field")
def bootstrap4_form_field_parser(parser, token):
    parameters = token.split_contents()
    if len(parameters) < 2:
        raise template.TemplateSyntaxError("{} needs the form field as first parameter.")
    form_field_variable = template.Variable(parameters[1])
    extra_parameters = {}
    for param in parameters[2:]:
        try:
            key, value = param.split("=", 1)
        except ValueError:
            raise template.TemplateSyntaxError("Parameter {} is invalid. Needs to have form key=value".format(param))
        if value[0] == value[-1] and value[0] in ("'", "\""):
            extra_parameters[key] = value[1:-1]
        else:
            extra_parameters[key] = template.Variable(value)
    return Bootstrap4FormField(form_field_variable, extra_parameters)


class Bootstrap4FormField(template.Node):
    def __init__(self, field_variable, params):
        self._field_variable = field_variable
        self._params = params

    @staticmethod
    def lookup(variable, context, default=""):
        try:
            return variable.resolve(context)
        except template.VariableDoesNotExist:
            return default

    @staticmethod
    def conditional_lookup(maybe_variable, context, default=""):
        if isinstance(maybe_variable, template.Variable):
            return Bootstrap4FormField.lookup(maybe_variable, context, default)
        else:
            return maybe_variable

    def render(self, context):
        field = self.lookup(self._field_variable, context, None)
        if field is None:
            raise template.TemplateSyntaxError("Form field variable could not be resolved: {}"
                                               .format(self._field_variable))

        css_class = "form-control"
        if field.errors:
            css_class += " is-invalid"
        attributes = {
            key: self.conditional_lookup(value, context) for key, value in self._params.items()
        }
        if "class" in attributes:
            attributes["class"] = css_class + " " + attributes["class"]
        else:
            attributes["class"] = css_class
        return field.as_widget(attrs=attributes)
