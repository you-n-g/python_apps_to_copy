#!/usr/bin/env python
#-*- coding:utf8 -*-

from django import forms
from models import Value, EField, ExtraEFormEFiledConfig
import fields
import validators
from django.db.models import Max, Count
from django.core.exceptions import ValidationError
from photologue.models import CommonImage 
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import  UploadedFile
from django.db.models import Q, Model
from django.http import QueryDict
import validation
from django.core.validators import EMPTY_VALUES


def _get_field_key(efield):
    return u"%s_%s" % (efield.pk, efield.key)

def _get_choices4efield(efield):
    field_class = getattr(fields, efield.field_type)
    choices =  [] if  (
        (efield.field_type in EField.MULT_CHOICES_FIELD) or 
        getattr(field_class, 'hide_blank_choice', False)
    ) else [((''), ('------'))]
    for choice in efield.choices.select_related().all():
        if efield.field_type == u'SimpleModelChoiceField':
            choices.append((u"%d-%d"%(choice.content_type.id,choice.object_id), choice.value))
        else:
            choices.append((choice.value, choice.value))
    return choices
    

class ProForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self._eform = kwargs.pop('eform', None)
        self._eobject = kwargs.pop('eobject', None) # eobject 可以是还未存储在数据库里的 eobject instance， 但是这个 instance 传入之前得先处理好它的属性， 比如 default_fill_eformset、default_display_eformset
        self._group = kwargs.pop('group', None)
        self._efields = self._eform.fields.all().order_by("-weight")
        self.initial_values = kwargs.pop('initial_values', None)
        self.is_multipart = False
        self.repeat_n = self._eform.repeat_n #form repeat 次数
        self.eform_name = self.name = self._eform.name
        self.instruction = self._eform.instruction
        super(ProForm, self).__init__(*args, **kwargs)
        # 让self.data 能修改，配合某些功能(那些功能希望修改传入的post data)
        if self.is_bound and isinstance(self.data, QueryDict):
            self.data._mutable = True

        efields = self._efields
        self.eobject_values = Value.objects.select_related('efield').filter(eobject = self._eobject, efield__in = efields)
        self.eobject_eform_groups = self._eobject.get_groups4eform(self._eform)
        # eform efield 的额外配置信息
        extra_eform_efield_configs = ExtraEFormEFiledConfig.objects.select_related('efield').filter(eform = self._eform)
        self._config_dict = {}
        for config in extra_eform_efield_configs:
            self._config_dict[config.efield.pk] = config
       
            
        key_value_dict = {}
        for value in self.initial_values or self.eobject_values.filter(group = self._group):
            field_key = _get_field_key(value.efield)
            if value.efield.field_type in EField.MULT_CHOICES_FIELD:
                v = key_value_dict.get(field_key, [])
                v.append(value.get_python_value())
                key_value_dict[field_key] = v
            elif value.efield.field_type == u'SimpleModelChoiceField':
                key_value_dict[field_key] = u"%d-%d"%(value.content_type.id,value.object_id)
            else:
                key_value_dict[field_key] = value.get_python_value()
        
        self._key_field_dict = {}
        self.choice_efields = choice_efields = efields.annotate(choice_n = Count('choices')).filter(choice_n__gt = 0)

        for efield in efields:
            field_key = _get_field_key(efield)
            self._key_field_dict[field_key] = efield
            if (not self.is_multipart) and efield.field_type in [u"ImageField",u"VideoField",u'FileField']:
                self.is_multipart = True
            self.fields[field_key] = getattr(fields, efield.field_type)() #TODO， 构建efield的时候需要加强, 加入widget等东西
            try:
                self.fields[field_key].widget.attrs['class']=efield.get_js_validator(initial_value = key_value_dict.get(field_key, None))
            except:
                pass
            self.fields[field_key].required = efield.required
            self.fields[field_key].label = efield.label
            self.fields[field_key].help_text = efield.help_text
            self.fields[field_key].initial = key_value_dict.get(field_key, None)
            # 因为ExtraEFormEFiledConfig的配置信息而变化
            config = self._config_dict.get(efield.pk, None)
            if config != None:
                if config.is_locked:
                    self.fields[field_key].widget.attrs['disabled'] = 'disabled'
                    if self.is_bound: # 如果可能涉及到验证的话， required就暂时为False，不能因为前台不传值而出错
                        self.fields[field_key].required = False
                        self.data[field_key] = self.fields[field_key].initial

            # 有choice加choice
            if efield in choice_efields:
                self.fields[field_key].choices = _get_choices4efield(efield)
                    
    def clean(self):
        for key, value in self.cleaned_data.items():
            efield = self._key_field_dict[key]
            
            # 是根据config做一些修改
            config = self._config_dict.get(efield.pk, None)
            if config != None:
                if config.is_locked:
                    self.cleaned_data[key] = self.fields[key].initial
                    self.fields[key].required = efield.required
                    continue

            if efield.field_type in EField.NEED_UPLOAD_FIELD and (not isinstance(value,UploadedFile)):
                continue # 文件没有重新上传，不需要验证

            if not efield.required and  value in EMPTY_VALUES:
                continue # 如果不是必填的， 她也没填 ，那就不验证 

            # 如果是新建group并且 目前有的再加一 > repeat_n 那就有问题啊！！
            if (self._group == None) and (len(self.eobject_eform_groups) + 1 > self.repeat_n):
                raise ValidationError(u"数量上限是%d" % self.repeat_n)

            validator_list = efield.get_validators()
            if validator_list.count()>0:               
                errors = []
                for val in validator_list:
                    # TODO  这里最好改成 json的 dict
                    if val.args:
                        try:
                            args = int(val.args)
                        except:
                            args=val.args
                        v = getattr(validators,val.validator)(args)
                    else:
                        v = getattr(validators,val.validator)
                    try:
                        v(value)
                    except ValidationError, e:
                        message = val.message if val.message else e.messages
                        self._errors[key] = self.error_class(message)
                        if key in self.cleaned_data:
                            del self.cleaned_data[key]
        #BEGIN 页面级别的验证
        if self._eform.validation:
            try:
                validation_func = getattr(validation, self._eform.validation)
            except AttributeError:
                pass
            else:
                is_valid, message = validation_func(self._eobject, self._eform, self.cleaned_data)
                if not is_valid:
                    raise ValidationError(message)
        #END   页面级别的验证
        return self.cleaned_data

    def save(self, *args, **kwargs):
        # 如果EObject还不是数据库里存储的， 那么就先存储一下
        if self._eobject.pk == None:
            self._eobject.save()

        #特别需要注意的！！！ 填写时，同一个项目在一个页面填写过一个field， 就不要让他在另外一个页面填写同一个field了 !!!!
        if self._group == None: # 如果是新建group，就为之赋值一个 group，取值规则是max(现有groups) + 1
            try:
                self._group = max(self.eobject_eform_groups) + 1
            except ValueError:
                self._group = 1
            
        new_values = []
        for key, value in self.cleaned_data.items():
            if value == None: continue # 非必填项，就跳过
            efield = self._key_field_dict[key]
            if efield.field_type in EField.MULT_CHOICES_FIELD:
                for item in value:
                    new_values.append(Value(
                            eobject = self._eobject,
                            efield = efield,
                            value = efield.get_db_value(item),
                            group = self._group
                    ))
            elif efield.field_type == u'SimpleModelChoiceField':
                content_type_id,object_id = value.split("-")[0],value.split("-")[1]
                new_values.append(Value(
                            eobject = self._eobject,
                            efield = efield,
                            content_type = ContentType.objects.get(pk=content_type_id),
                            object_id = object_id,
                            group = self._group
                ))

            elif efield.field_type in [u"VideoField",u'FileField']:
                new_values.append(Value(
                        eobject = self._eobject,
                        efield = efield,
                        vfile = value,
                        group = self._group
                ))
            elif efield.field_type == u"ImageField":
                commonImage = CommonImage.objects.create(image=value) if isinstance(value, UploadedFile) else  value
                new_values.append(Value(
                        eobject = self._eobject,
                        efield = efield,
                        content_type = ContentType.objects.get_for_model(commonImage),
                        object_id = commonImage.id,
                        group = self._group
                ))
            else:
                new_values.append(Value(
                        eobject = self._eobject,
                        efield = efield,
                        value = efield.get_db_value(value),
                        group = self._group
                ))

        self.eobject_values.filter(group = self._group, eobject = self._eobject).delete() # 初始值可以是其他的 eobject的， 所以这个删除必须加上  eobject.self._eobject, 否则可能将别人的数值删除
        Value.objects.bulk_create(new_values)
        return self._eobject

class FilterEObjectForm(forms.Form):
    '''
        我是根据EField来筛选 **指向EObject** 的 instance 的！！！
    '''
    def __init__(self, *args, **kwargs):
        self._efields = kwargs.pop('efields', None)
        self._eobject_instances = kwargs.pop('eobject_instances', None)
        self._treat_multi_as_single = kwargs.pop('treat_multi_as_single', True) # 是否把多选框当成单选框来处理
        # _extra_filters 是想强塞进来的筛选条件， 格式如下
        # [{key: value}, {key: value}...]
        self._extra_filters = kwargs.pop('extra_filters', [])
        self._foreignkey_name = kwargs.pop('foreignkey_name', 'eobject')
        super(FilterEObjectForm, self).__init__(*args, **kwargs)
        for efield in self._efields:
            if efield.field_type in  EField.SUPPORT_SEARCH_FIELD:
                field_key = _get_field_key(efield)
                #TODO， 构建efield的时候需要加强, 加入widget等东西
                if (efield.field_type in EField.MULT_CHOICES_FIELD) and self._treat_multi_as_single:
                    efield.field_type =  "ChoiceField"
                self.fields[field_key] = getattr(fields, efield.field_type)()
                self.fields[field_key].efield = efield # 记录 efield
                self.fields[field_key].required = False
                self.fields[field_key].label = efield.label
                if efield.choices.exists():
                    self.fields[field_key].choices = _get_choices4efield(efield)

    def get_result(self):
        if self._eobject_instances == None:
            return []
        if self.is_valid():
            result = self._eobject_instances
            for field_key, value in self.cleaned_data.items():
                if value:
                    query = Q(**{
                        '%s__value__efield' % self._foreignkey_name :  self.fields[field_key].efield
                    })
                    if self.fields[field_key].efield.field_type == 'SimpleModelChoiceField':
                        content_type_id,object_id = value.split("-")[0],value.split("-")[1]
                        query = query & Q(**{
                            '%s__value__content_type' % self._foreignkey_name : content_type_id
                        }) & Q(**{
                            '%s__value__object_id' %  self._foreignkey_name : object_id
                        })
                    elif self.fields[field_key].efield.field_type == 'ChoiceField':
                        query = query & Q(**{
                            '%s__value__value'%  self._foreignkey_name : value
                        })
                    else:
                        query = query & Q(**{
                            '%s__value__value__contains'%  self._foreignkey_name : value
                        })
                    for query_dic in self._extra_filters:
                        query = query & Q(**query_dic)
                    result = result.filter(query)
            return result.distinct()
        return self._eobject_instances.all()
