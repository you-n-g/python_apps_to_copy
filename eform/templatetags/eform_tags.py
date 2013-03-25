# -*- coding:utf8 -*-
from django.template import TemplateSyntaxError, VariableDoesNotExist, Node
from django.template import Library, Variable, loader, Context

from django import template
from eform.utils import get_eform_sidebar, get_display_info as get_display_info_utils
import os
from eform.models import EField
register = Library()

class EFormSideBarNode(Node):
    def __init__(self, eobject, eformset, current_form, template):
        self.eformset = eformset
        self.current_form = current_form
        self.eobject = eobject
        self.template = template

    def render(self, context):
        eformset = self.eformset.resolve(context)
        current_form = self.current_form.resolve(context)
        eobject = self.eobject.resolve(context)
        template = self.template.resolve(context)

        request = context.get('request', None)
        eform_sidebar = get_eform_sidebar(eobject, eformset, current_form)
        
        t = loader.get_template(template)

        context.update(locals())
        code_context = Context(context, autoescape=context.autoescape)
        return t.render(code_context)

@register.tag
def eform_sidebar(parser, token):
    bits = token.split_contents()
    remaining_bits = bits[1:]

    if len(remaining_bits) != 4:
        raise TemplateSyntaxError("%r 需要4个参数" % bits[0])

    kwargs = {
        'eobject' : parser.compile_filter(remaining_bits[0]),
        'eformset' : parser.compile_filter(remaining_bits[1]),
        'current_form' : parser.compile_filter(remaining_bits[2]),
        'template' : parser.compile_filter(remaining_bits[3]),
    }

    return EFormSideBarNode(**kwargs)

class ValueDisplayNode(Node):
    def __init__(self,value,template_name):
        self.value = value
        self.template_name=template_name
    def render(self, context):
        value = self.value.resolve(context)
        value_type = value.efield.field_type
        python_value = value.get_python_value()
        if value_type not in EField.SPECIAL_DISPLAY_FIELD:
            return python_value
        template_name = self.template_name.resolve(context)
        request = context.get('request', None)
        t = loader.get_template(template_name)

        context.update(locals())
        code_context = Context(context, autoescape=context.autoescape)
        return t.render(code_context)

@register.tag
def value_display_in_template(parser, token):
    "{%value_display_in_template value template_name%}"
    bits = token.split_contents()
    remaining_bits = bits[1:]

    if len(remaining_bits) != 2:
        raise TemplateSyntaxError("%r 需要2个参数" % bits[0]) 

    kwargs = {
        "value":parser.compile_filter(remaining_bits[0]),
        'template_name' : parser.compile_filter(remaining_bits[1]),
    }
    return ValueDisplayNode(**kwargs)


@register.filter
def get_display_info(eobject, eformset):
    return get_display_info_utils(eobject, eformset)
