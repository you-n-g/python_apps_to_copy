#!/usr/bin/env python
#-*- coding:utf8 -*-

from forms import ProForm, Value
from django.shortcuts import get_object_or_404
from django.db.models import Max
from models import get_newest_value4efield, get_string_from_values, EForm, EObject, get_string_from_efield4eobject, clear_eobject_cache, get_python_values4eobject
from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.core.cache import cache
from eform.models import EFormItem, get_eobject_key
import urllib

def process_eform_request(request, eobject, eform):
    '''
        处理表单
    '''
    form = render_form(request.POST, eobject = eobject, eform = eform)
    if form.is_valid():
        form.save()


def get_eform_sidebar(eobject, eformset, current_form = None):
    '''
        计算侧边栏
    '''
    # TODO 换成redis缓存？ 
    ret = []
    for efi in eformset.eformitem_set.all():
        if efi.forms.exists() or efi.kind == "always_show":
            eform = efi.get_eform(eobject)
            ret.append((eform or efi, eform and eform.is_complete(eobject), eform == current_form, eform != None))
    return ret

def get_eform_display_info(eobject, eform):
    '''
        返回值如
        [
            [ # Group n
             (field1, [value1.1, value1.2]),
             (field2, [value2]),
             ...
            ], 
            [ # Group n + 1
             (field1, [value1]),
             (field2, [value2]),
             ...
            ]
            ...
        ]
    '''

    fields_groups = []
    group = None
    values = eobject.value_set.filter(efield__eform = eform).select_related('efield').all().order_by('group', '-efield__weight', 'efield__pk')
    fgr = []
    for value in values:
        if value.group != group:
            group = value.group
            if fgr != []: 
                fields_groups.append(fgr)
            fgr = []
        if fgr and fgr[-1][0] == value.efield:
            fgr[-1][1].append(value)
        else:
            fgr.append((value.efield, [value]))
    if fgr: fields_groups.append(fgr)
    return fields_groups

def get_eform_value_dict_list(eobject, eform):
    cache_key = get_eobject_key(eobject, suffix = 'eform_dict_list_values'),
    dict_key = u"eform_key_%s" % eform.key
    eobject_dict = cache.get(cache_key)
    if eobject_dict == None:
        eobject_dict = {}
    if not eobject_dict.has_key(dict_key):
        eform_values_dict_list= []
        for group_values in  get_eform_display_info(eobject, eform):
            values_dict = {}
            for field, values in group_values:
                values_dict[field.key] = values
            eform_values_dict_list.append(values_dict)
        eobject_dict[dict_key] = eform_values_dict_list
        cache.set(cache_key, eobject_dict, 1800)
    return eobject_dict[dict_key]



    return eobject_dict[dict_key]

def get_display_info(eobject, eformset):
    ''' 
        返回值如, 两个元素 
            第一个是 eform 的普通字段, 一个列表
            第二个是 special 的字段, 一个字典

        (
          # 表示普通的 eform
          [
            (eform, [
                        [ # Group n
                         (field1, [value1.1, value1.2]),
                         (field2, [value2]),
                         ...
                        ], 
                        [ # Group n + 1
                         (field1, [value1]),
                         (field2, [value2]),
                         ...
                        ]
                        ...
                    ]
            ),
            ...
          ], 

          # 表示特殊的 eform
          {
              'image': (eform, [
                          [ # Group n
                           (field1, [value1.1, value1.2]),
                           (field2, [value2]),
                           ...
                          ], 
                          [ # Group n + 1
                           (field1, [value1]),
                           (field2, [value2]),
                           ...
                          ]
                          ...
                      ]
              ),
              'video': ...
              ...
          }
        )
    '''
    normal_eforms = []
    special_eforms = {} # 目前 默认 一个项目只能有一组照片。。
    for eformitem in eformset.eformitem_set.all():
        eform = eformitem.get_eform(eobject)
        if eform == None: continue

        fields_groups = get_eform_display_info(eobject, eform)

        # 根据eform_type处理special_eforms
        eform_type = eform.get_eform_type()
        if eform_type  == 'normal':
            normal_eforms.append((eform,  fields_groups))
        else:
            eforms = special_eforms.get(eform_type, [])
            eforms.append((eform,  fields_groups))
            special_eforms[eform_type] = eforms
    return normal_eforms, special_eforms


def _get_valid_redirect_url(request, obj, eobj, eform, eformset, with_action_name=False):
    # BEGIN 获得下一个EForm, valid_redirect_url 表示表单验证通过后会跳转到哪里去
    eformitem = EFormItem.objects.get(forms = eform, eformset = eformset)
    next_eform = eformitem.get_next_eform(eobj)
    valid_redirect_url = obj.get_edit_eform_url(request, next_eform) if next_eform else obj.get_owner_view_url(request)  
    # END   获得下一个EForm, valid_redirect_url 表示表单验证通过后会跳转到哪里去
    if with_action_name:
        next_action_name = (u'填写%s' %  next_eform.name) if next_eform else u'预览信息'
        return valid_redirect_url, next_action_name
    else:
        return valid_redirect_url


def _fill_eform_view(request, obj, eobj, eformset, template, 
        eform_id = None, 
        group = None,
        redirect_url =None,
        context_dict = {}, 
        get_edit_eform_url_func = "get_edit_eform_url",
        get_owner_view_url_func = "get_owner_view_url",
        initial_values = None,
    ):
    '''
        填写EForm的时候有非常多的重复代码，重复的部分都由我来收着吧...
        我会返回 我觉得应该返回的 response 和 form， 方便大家来查看
    '''
    if redirect_url:
        redirect_url = redirect_url
    else:
        redirect_url = request.META.get('HTTP_REFERER', '/')
    #1) 如果没有制定eform_id 就帮他找一个并重定向
    if eform_id == None:
        eform = eformset.get_first_available_eform(eobj)
        # 这里我假设配置表单的人不会坑我，至少有一个表单是可以填写的。。
        return HttpResponseRedirect(getattr(obj, get_edit_eform_url_func)(request, eform)), None

    #2) 如果 eform 没有通过 logic item 就跳到其他页面
    eform = get_object_or_404(EForm, pk = eform_id, eformitem__eformset = eformset) 
    if not eform.test_logic_item(eobj):
        messages.info(request, u'请先完善其他信息')
        return HttpResponseRedirect(redirect_url), None

    #3) 如果指定了group 但是 group不存在就跳转到新加的页面
    groups = eobj.get_groups4eform(eform)
    if group != None : group = int(group)
    if group != None and  not(group in groups):
        return HttpResponseRedirect(getattr(obj, get_edit_eform_url_func)(request, eform)), None

    #4) 如果是那种只填写一次的页面 还是新建的， 就检查一下是否已经填写了， 已经填写了的话，就直接把group赋值成相应的值
    values = Value.objects.filter(eobject = eobj, efield__in = eform.fields.all())
    if eform.repeat_n == 1 and group == None:
        group = values.aggregate(Max('group'))['group__max']

    #把所有表单有多个form的值全部去出来
    if eform.repeat_n>1:
        eform_values = get_eform_display_info(eobject=eobj,eform = eform)

    #1、2、3、4 共同保证了有 eform ， 并且可以填，如果是编辑一定有group， 否则就是添加
    if request.POST.get('delete_group_info', None) == None:
        # 普通的表单保存
        form = ProForm(request.POST or None, request.FILES or None,eobject = eobj, eform = eform, group = group, initial_values = initial_values)
        if form.is_valid():
            form.save()
            clear_eobject_cache(eobj)
            messages.info(request, u'保存%s成功' % eform.name)
            if eform.repeat_n == 1 and (eform.get_eform_type() not in ('image', )): # 如果是 只填写一遍的页面 并且  不是 传图页面， 就跳转
                redirect_url = _get_valid_redirect_url(request, obj, eobj, eform, eformset) or redirect_url
            elif eform.repeat_n > 1:
                # 如果是填写多个的页面，就回到编辑整个 eform的页面。
                redirect_url = getattr(obj, get_edit_eform_url_func)(request, eform)
            return HttpResponseRedirect(redirect_url), form
                
    else:
        if group != None:
            values.filter(group = group).delete()
            clear_eobject_cache(eobj)
        messages.info(request, u'成功删除%s！' % eform.name)
        return HttpResponseRedirect(redirect_url), None
    
    valid_redirect_url = _get_valid_redirect_url(request, obj, eobj, eform, eformset)
    context_dict.update(locals())
    return render(request, template, context_dict), form

def fill_eform_view(*args, **kwargs):
    '''
        我是给外部调用的，我做了一个封装，如果  return_response_only = True 的话， 就只返回 reponse， 否则就返回 response 和 eform
        return_response_only 默认值为True
    '''
    return_response_only = kwargs.pop('return_response_only', True)
    response, form = _fill_eform_view(*args, **kwargs)
    if return_response_only:
        return response
    else:
        return response, form

def copy_eobject(from_eobject, to_eobject = None, eformset = None):
    '''
        拷贝 eobject， 可以指定拷贝到哪个 eobject 上， 可以指定 eformset的哪些字段。
    '''
    if to_eobject == None:
        to_eobject = EObject.objects.create(
            default_display_eformset = from_eobject.default_display_eformset,
            default_fill_eformset = from_eobject.default_fill_eformset,
        )
    else:
        Value.objects.filter(eobject = to_eobject).delete()
    query = {
        'eobject': from_eobject,
    }
    if eformset != None: query['efield__eform__eformitem__eformset'] = eformset
    values = []
    for value in Value.objects.filter(**query):
        value.pk = None
        value.eobject = to_eobject
        values.append(value)
    Value.objects.bulk_create(values)
    clear_eobject_cache(to_eobject)
    return to_eobject
