#!/usr/bin/env python
#-*- coding:utf8 -*-
'''
eform依赖于以下app
photologue
tools.utils 记得带上 magic
tools.memcached
resource_lock
flowplayer
tagging, xiaosai里的tagging是修改过的，我推荐去那里面改

前台文件
拷贝bootstrap : 话说为什么我们别的代码中的bootstrap 的 bootstrap 的 line 157 的 width:auto;被注释掉了
拷贝validate

记得弄一下 datetimepicker的 next 和 prev 的图片
'''


# -----------------最简使用 使用方法 ， 针对只有一页内容的eformset， 也不需要前台验证 ------------------

from tools.utils import lock_view_when_post
from eform.forms import ProForm

@lock_view_when_post("XXXX")
def XXX(request):
    XXX # 找一个方法获得XXX
    eobj = XXX.XXX_eobject
    form = ProForm(request.POST or None, eobject = eobj, eform = eobj.default_fill_eformset.get_first_available_eform(eobj), group = XXX, initial_values = Values.XXX.filter())
    # group 如果是 None 的话， 就一定是新建， 否则你得去找Group (这是因为EForm同一表单是支持填写多遍的，你必须指定到底修改的是哪个Group)
    if form.is_valid():
        eobj = form.save()
        # 如果还需保存 xxx 请如下
        XXX.XXX_eobject = eobj
        XXX.save()
    return render(request, "tree_flow/add_org.html", locals())
"""  html

<form action="XXX" class="form-horizontal" method="POST" >
    {% csrf_token %}
    {% include "eform/form_fields.html" %}
    <input type="submit" value="XXX">
</form>
"""


# -----------------进阶使用 使用方法 ， 针对有多页内容的eformset------------------
# BEGIN urls.py
#EDIT
url(r'^XXX/(?P<XXX_id>\d+)/$', 'process_XXX', name='process_XXX'),
url(r'^XXX/(?P<XXX_id>\d+)/(?P<eform_id>\d+)/$', 'process_XXX', name='process_XXX'),
url(r'^XXX/(?P<XXX_id>\d+)/(?P<eform_id>\d+)/(?P<group>\d+)/$', 'process_XXX', name='process_XXX'),
#EDIT
url(r'^view/(?P<XXX_id>\d+)/$', 'view_XXX', name='view_XXX'),
# END   urls.py


# BEGIN models.py
class XXX(models.Model):
    def get_edit_eform_url(self, request,  eform):
        '''
            获取编辑 eform 的url
        '''
        return reverse('process_XXX', kwargs={'XXX_id': self.id, 'eform_id': eform.id})

    def get_owner_view_url(self, request):
        '''
            获取 编辑者 自己查看的页面
        '''
        return reverse('view_XXX', kwargs={'XXX_id': self.id})
# END   models.py


# BEGIN views.py
from tools.utils import lock_view_when_post
from eform.utils import fill_eform_view


@lock_view_when_post("XXXX")
def process_XXX(request, XXX_id, **kwargs):
    xxx = get_object_or_404(XXX, pk=XXX_id)
    # TODO permission examine
    eobject = xxx.xxx_eobject
    eformset = eobject.default_fill_eformset
    eform_id = kwargs.get('eform_id', None)
    group = kwargs.get('group', None)

    return fill_eform_view(
        request,
        obj=xxx,
        eobj=eobject,
        eformset=eformset,
        template="XXX.html",
        eform_id=eform_id,
        group=group,
        context_dict={'xxx': xxx},
        initial_values=Values.XXX.filter()
    )

def view_XXX(request, XXX_id):
    xxx = get_object_or_404(XXX, pk = XXX_id)
    # TODO permission examine
    eobject = xxx.xxx_eobject
    eformset = eobject.default_display_eformset
    return render(request, 'view_XXX.html', locals())

# END   views.py

""" html
{% load eform_tags %}

    <script src="{{STATIC_URL}}plugins/jquery.validate.min.js" type="text/javascript"></script>
    <script src="{{STATIC_URL}}plugins/jquery.metadata.js" type="text/javascript"></script>

    <form action="." method="POST" {% if form.is_multipart %}enctype="multipart/form-data"{% endif %} class="form-horizontal need_validate eform_form">
    {% csrf_token %}
    {%if eform.repeat_n > 1 and not group%}
        {% include "eform/form_without_formname.html" %}
    {%else%}
        {% include "eform/form_without_form.html" %}
    {%endif%}
    </form>

如果要多页或者能添加删除信息的话， 在form之前加上以下内容

    {%if eform.repeat_n > 1 and not group %}
        {%if form.name%}<legend class="survey_title">{{form.name}}</legend>{%endif%}
        {% comment %}
        {%if not group and  eform_values|length > 0%}
            {% if not form.is_bound or form.is_valid %}
            <a href="javascript:void(0)" onclick="show_form();" class="add_form mlrB col-1">添加</a>  
            {% endif %}
        {% endif %}
        {% endcomment %}
        <div class="mtA">
        {% if eform.get_eform_type == "image"%}
            {%for gv in eform_values%}
                <div class="col-1-5"> 
                {%for efield, vs in gv%}
                <div class="col-1 taC">
                    {% for v in vs %}
                    {%value_display_in_template v "eform/value_display.html"%}                       
                    {% endfor %}
                </div>
                <div class="col-1 taC">
                    <form action="{%url process_XXX XXX=XXX.id eform_id=eform.id group=gv.0.1.0.group %}" method="POST" style="display: inline-block;"  class="submit_confirm">
                    {% csrf_token %}                         
                    <button type="submit"  name="delete_group_info">删除</button> 
                </form>
                </div>
                {%endfor%}
                </div> 
            {%endfor%}
        {% else %}
            {%for gv in eform_values%}
                <div class="pdC itsthetable">
                    <table>
                        <caption>{{eform.name}}
                            <a href="{%url process_XXX XXX=XXX.id eform_id=eform.id group=gv.0.1.0.group %}" title="修改">修改</a>
                            <form action="{%url process_XXX XXX=XXX.id eform_id=eform.id group=gv.0.1.0.group %}" method="POST" style="display: inline-block;"  class="submit_confirm">
                                {% csrf_token %}                         
                                <button type="submit"  name="delete_group_info">删除</button> 
                            </form>
                        </caption>
                        <tbody>
                        {%for efield, vs in gv%}
                        <tr class="{% if forloop.counter|divisibleby:2 %}even{% else %}odd{% endif %}">
                            <th class="col-1-6">{{efield.label}}</th>
                            <td class="col-2-3">                      
                            {% for v in vs %}
                            {%value_display_in_template v "eform/value_display.html"%}
                            {% endfor %}
                            </td>
                        </tr>
                        {%endfor%}
                        </tbody>
                    </table>
                </div>
            {%endfor%}
        {% endif %}
        </div>
        <p></p>
        <script type="text/javascript">
            function show_form(){
                $("form.form-horizontal").show();
                $(".add_form").hide();
            }
            {% comment %}
            $(function(){
                {%if not group and eform_values|length > 0 %}
                    {% if not form.is_bound or form.is_valid %}
                    $("form.form-horizontal").hide();
                    {% endif %}
                {%endif%}
            })
            {% endcomment %}
            $(function(){
                $('.submit_confirm').submit(function(){
                    return confirm("您确定要删除么");
                });
            });
        </script>
    {%endif%}

如果希望加入sidebar，  需要加上如下templatetag

    {% eform_sidebar eobj eformset eform "XXX/process_XXXX_sidebar.html" %}

然后 "XXX/process_XXXX_sidebar.html"  内容如下

<ul class="steptab">
    {% for eform,is_completed,is_current,has_link in  eform_sidebar %}
    <li class="{% if is_current %}on{% endif %} {% if forloop.last %}final{% endif %}">
            {%if not forloop.first%}<em class="left"></em>{%endif%}
            <span><a class="item" {% if has_link %}href="{% url process_XXX eform_id=eform.id %}"{% endif %} title="">
            {{eform}}({{forloop.counter}}/{{eform_sidebar|length}})
            {% if is_completed %}
                <b style="color:green">(已完成)</b> 
            {% else %}
                <b style="color:#F77">(未完成)</b>
            {% endif %}
            &nbsp;
            </a></span>
            {%if not forloop.last%}<em></em>{%endif%}
        </li>
    {% endfor %}
</ul>
<script type="text/javascript">
    $(function(){
            $(".steptab .on").next().addClass("second");
    });
</script>

样式如下

.steptab{ /* border:1px solid #ccc; float:left; */ font-size:12px; line-height:1.0;font-size: 14px;}
.steptab li{ background:#f5f5f5; float:left; width:180px; height:30px; overflow:hidden; margin-right:15px;margin-bottom: 0px;}
.steptab li.final{margin-bottom: 0px;margin-right:0px;}
.steptab li span{ position:absolute; padding:6px 20px 0 20px;}
.steptab li em{ margin-left:180px; background:#FF6633;position:absolute; border:15px solid #f5f5f5; border-left:#f5f5f5; height:0px; overflow:hidden;}
.steptab li .left{ margin-left:0; border:15px solid #f5f5f5; border-left:15px solid #ccc;}
.steptab li.second .left{ margin-left:0; border:15px solid #f5f5f5; border-left:15px solid #f5f5f5;}
.steptab .on{ background:#CDF;font-weight: bold;}
.steptab .on em{ background:#FF6633;border-left:15px solid #CDF;}
.steptab .on .left{border-top:15px solid #CDF; border-bottom:15px solid #CDF; border-right:15px solid #CDF;border-left:15px solid #f5f5f5;}
.steptab li.on a{color:#606060;}
"""

# 搜索 eform 的使用方法
from eform.forms import FilterEObjectForm
form = FilterEObjectForm(request.GET, efields = efields, eobject_instances = XXXs, foreignkey_name = 'eobject')

