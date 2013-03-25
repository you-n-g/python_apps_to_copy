#!/usr/bin/env python
#-*- coding:utf8 -*-

from django.forms import CharField, FileField as DjangoFileField, ChoiceField, MultipleChoiceField as DjangoMultipleChoiceField, ModelChoiceField, ImageField as DjangoImageField
from django.forms import DateField as DjangoDateField, TimeField as  DjangoTimeField,DateTimeField as DjangoDateTimeField
from django import forms
from widgets import ImageInput, NiceFileInput,DateWidget,TimeWidget,DateTimeWidget
#from tagging.widgets import TagAutocompleteTagIt # 因为在本项目里没用到，暂时注释掉
from tagging.forms import TagField  as OtherTagField

'''
    我们的一些约定
    * hide_blank_choice :: 表示一些选择input是否允许空的选择
'''
class ImageField(DjangoImageField):
    widget = ImageInput

class VideoField(DjangoFileField):
	pass

class FileField(DjangoFileField):
    widget = NiceFileInput

class SimpleModelChoiceField(ChoiceField):
	pass

class MultipleChoiceField(DjangoMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

class TextField(CharField):
    widget = forms.Textarea

'''# 因为在本项目里没用到，暂时注释掉
class TagField(OtherTagField):
    widget = TagAutocompleteTagIt
'''

class DateField(DjangoDateField):
    widget =DateWidget

class TimeField(DjangoTimeField):
    widget = TimeWidget

class DateTimeField(DjangoDateTimeField):
    widget = DateTimeWidget

class RadioChoiceField(ChoiceField):
    hide_blank_choice = True
    widget = forms.RadioSelect
