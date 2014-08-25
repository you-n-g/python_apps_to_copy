#!/usr/bin/env python
#-*- coding:utf8 -*-

from django.utils.safestring import mark_safe
from django.utils.html import escape, conditional_escape
from django.forms.widgets import ClearableFileInput, FileInput, CheckboxInput, FILE_INPUT_CONTRADICTION
from django.utils.encoding import force_unicode
from photologue.models import CommonImage
from django.conf import settings
from django.utils.translation import ugettext as _
import os
from django import forms
from datetime import datetime
from django.forms.widgets import MultiWidget, SplitDateTimeWidget
from django.forms.util import to_current_timezone, flatatt


class ImageInput(ClearableFileInput):
    initial_text = u'当前图片'
    template_with_initial = '''
            %(initial_text)s: %(initial)s
        <br/>
            %(input_text)s: %(input)s
'''
    initial_template = '''
    <a href="%(get_display_url)s" class="highslide" onclick="return hs.expand(this)">
            <img src="%(get_100_100_url)s" alt="" title="Click to enlarge" />
    </a>
'''

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
        }
        substitutions['input'] = FileInput.render(self, name, value, attrs)
        template = u'%(input)s'
        if value and isinstance(value, CommonImage):
            template = self.template_with_initial
            substitutions['initial'] = (self.initial_template % {
                "get_display_url": value.get_display_url(),
                "get_100_100_url": value.get_100_100_url(),
            })
        return mark_safe(template % substitutions)

    class Media:
        js = ('%scommon/js/highslide-with-gallery.min.js' % settings.STATIC_URL,
            '%scommon/js/image_display_header.js' % settings.STATIC_URL)
        css = {
            'all': ('%scommon/css/highslide.css' % settings.STATIC_URL,)
        }


class NiceFileInput(ClearableFileInput):
    initial_text = u'目前'
    template_with_initial = '''
            %(initial_text)s: %(initial)s
        <br/>
            %(input_text)s: %(input)s
'''
    initial_template = '''
    <a href="%(url)s">
        %(name)s
    </a>
'''

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
        }
        substitutions['input'] = FileInput.render(self, name, value, attrs)
        template = u'%(input)s'
        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = (self.initial_template % {
                "url": value.url,
                "name": u'点击下载',
            })
        return mark_safe(template % substitutions)


class DateWidget(forms.DateInput):

    "copy form jquery tool"
    class Media:
        js = ("%splugins/datetimeinput/jquery.tools_dateinput.min.js" % settings.STATIC_URL,)
        css = {
            'all': ["%splugins/datetimeinput/datetime_style.css" % settings.STATIC_URL],
        }

    def __init__(self, attrs=None, format=None):
        final_attrs = {}
        if attrs is not None:
            final_attrs.update(attrs)
        super(DateWidget, self).__init__(attrs=final_attrs, format=format)

    def render(self, name, value, attrs={}):
        final_attrs = self.build_attrs(attrs, name=name)
        if value:
            if isinstance(value, (str, unicode)):
                try:
                    d_value = datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    d_value = value
            else:
                d_value = value
            final_attrs["value"] = d_value
        else:
            value = ""
            final_attrs["value"] = ""
        year_range = '[-100,50]'
        return mark_safe(u"<input type='text' %s ></input> \
<script type='text/javascript'>$(function(){\
$.tools.dateinput.localize('zh', {months: '一月,二月,三月,四月,五月,六月,七月,八月,九月,十月,十一月,十二月',\
shortMonths:'一月,二月,三月,四月,五月,六月,七月,八月,九月,十月,十一月,十二月',\
days:'星期日,星期一,星期二,星期三,星期四,星期五,星期六',shortDays:'周日,周一,周二,周三,周四,周五,周六'});\
$(':input[name=%s]').dateinput({format:'yyyy-mm-dd',\
selectors: true, speed: 'fast', value:'%s' ,yearRange:%s,lang:'zh',firstDay: 1 });})\
</script>" % (flatatt(final_attrs), name, final_attrs["value"], year_range))


class TimeWidget(forms.TimeInput):
    def __init__(self, attrs=None, format="%H:%M", step=5):
        self.step = step
        final_attrs = {}
        if attrs is not None:
            final_attrs.update(attrs)
        super(TimeWidget, self).__init__(attrs=final_attrs, format=format)

    class Media:
        js = ("%splugins/datetimeinput/jquery.timePicker.min.js" % settings.STATIC_URL,)
        css = {
            'all': ["%splugins/datetimeinput/datetime_style.css" % settings.STATIC_URL],
        }

    def render(self, name, value, attrs={}):
        final_attrs = self.build_attrs(attrs, name=name)
        if value is None:
            value = ""
        else:
            value = str(value)  # because value may be instance of datetime.time
            value = ":".join(value.split(":")[:2])
        final_attrs['value'] = value
        start_time = "00:00"
        end_time = "23:59"
        return mark_safe(u"<input type='text' %s ></input>\
            <script type='text/javascript'>$(function(){\
              $('input[name=%s]').timePicker({show24Hours:true,separator:':',step:%d,startTime:'%s',endTime:'%s'});   \
            })</script>" % (flatatt(final_attrs), name, self.step, start_time, end_time))


class DateTimeWidget(SplitDateTimeWidget):
    def __init__(self, attrs=None):
        widgets = (DateWidget, TimeWidget)
        MultiWidget.__init__(self, widgets, attrs)

    def decompress(self, value):
        if value:
            value = to_current_timezone(value)
            if isinstance(value, unicode):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    return [value.date().strftime("%Y-%m-%d"), value.time().strftime("%H:%M")]
                except ValueError:
                    pass
        return ["", ""]

    def format_output(self, rendered_widgets):
        return mark_safe(u"<p class='datetimewidget'>%s %s</p>" % (rendered_widgets[0], rendered_widgets[1]))


class VideoInput(ClearableFileInput):
    template_with_initial = \
        u'<div class="fileinput"><p>%(initial_text)s: %(initial)s </p><p>%(input_text)s: %(input)s</p></div>'
    initial_template = '''
<a href="%(url)s"
     style="display:block;width:470;height:300px; margin-left:auto; margin-right:auto"
     id="%(id)s">
</a>
<script>
    flowplayer("%(id)s", {src: '%(STATIC_URL)scommon/flowplayer/flowplayer-3.2.7.swf',\
wmode: 'transparent',width:470,height:300}, {
                clip:{
                    autoPlay:false,
                    autoBuffering:true,
                    start:20,
                    urlEncoding: true
                }
    });
</script>
'''

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = u'%(input)s'
        substitutions['input'] = FileInput.render(self, name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = (self.initial_template % {
                "url": escape(value.url),
                "id": 'project_video%d' % id(self),
                "STATIC_URL": settings.STATIC_URL,
            })
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)

    class Media:
        js = ('%scommon/flowplayer/flowplayer-3.2.6.min.js' % settings.STATIC_URL,)
