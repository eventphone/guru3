import string
import random

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

register = template.Library()


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@register.filter(name='cssclass')
def cssclass(value, arg):
    return value.as_widget(attrs={'class': arg})


@register.filter(name='bootstrap_css_style')
def bootstrap_css_style(value, style):
    css_class = "form-control"
    if value.errors:
        css_class += " is-invalid"
    return value.as_widget(attrs={"class": css_class, "style": style})


@register.simple_tag(name="form_post_button", takes_context=True)
def form_post_button_tag(context, glyph, description, delete_view, **kwargs):
    next = kwargs.pop("next", None)
    urlkwargs = kwargs
    targetUrl = escape(reverse(delete_view, kwargs=urlkwargs))
    csrf_token = context.get('csrf_token', None)
    if next is not None:
        next_url_tag = "<input type=\"hidden\" name=\"next\" value=\"" + escape(next) + "\" />"
    else:
        next_url_tag = ""
    return mark_safe(u"""<form action="{}" method="POST" style="display: inline">
<input type="hidden" name="csrfmiddlewaretoken" value="{}">
<button type="submit" title="{}" class="oi oi-{}" ></button>{}
</form>""".format(targetUrl, csrf_token, description, glyph, next_url_tag))


class AutoHelperCrispyFormNode(CrispyFormNode):
    def __init__(self, *args, **kwargs):
        self.submit_button_name = kwargs["submit_button_name"]
        del kwargs["submit_button_name"]
        super(AutoHelperCrispyFormNode, self).__init__(*args, **kwargs)

    def render(self, context):
        # retrieve our form and put a helper on it if not present
        form = template.Variable(self.form)
        theForm = form.resolve(context)
        if not hasattr(theForm, "helper"):
            theForm.helper = FormHelper()
            theForm.helper.add_input(Submit(self.submit_button_name, self.submit_button_name))
        return super(AutoHelperCrispyFormNode, self).render(context)

@register.tag(name="simple_crispy")
def fancy_crispy_tag(parser, token):
    try:
        split = token.split_contents()
        if len(split) == 2:
            split.append("\"Submit\"")
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments: <form> \"<submit name>\"" % token.contents.split()[0])

    tag_name, form, submit_name = split
    if submit_name[0] != "\"" or submit_name[-1] != "\"":
        raise template.TemplateSyntaxError("%r tag requires the second parameter to be a string" % token.contents.split()[0])
    submit_name = submit_name.rstrip("\"").lstrip("\"")

    return AutoHelperCrispyFormNode(form, None, template_pack=settings.CRISPY_TEMPLATE_PACK, submit_button_name = submit_name)