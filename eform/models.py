#!/usr/bin/env python
#-*- coding:utf8 -*-

from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models import Max, Count, Q, F

from tools.utils import get_file_path, cache_object_attr
from django.utils import simplejson
from django.core.cache import cache

try:
    from tagging.fields import TagField
    from tagging.models import Tag
except ImportError:
    class TagField(models.CharField):
        def __init__(self, *args, **kwargs):
            default_kwargs = {'max_length': 255, 'blank': True}
            default_kwargs.update(kwargs)
            super(TagField, self).__init__(*args, **default_kwargs)
        def get_internal_type(self):
            return 'CharField'

# BEGIN  我们是 工具函数#{{{
def get_eobject_key(eobject, suffix = ''):
    return u"eobject_key_%d_%s" % (eobject.pk, suffix)

def get_newest_value4efield(eobject, efield):
    if efield == None: return Value.objects.none()
    values = Value.objects.filter(efield = efield, eobject = eobject)
    max_group = values.aggregate(Max('group'))['group__max']
    return values.filter(group = max_group)

def get_newest_value4key(eobject, key):
    values = Value.objects.filter(efield__key = key, eobject = eobject)
    max_group = values.aggregate(Max('group'))['group__max']
    return values.filter(group = max_group)

def get_string_from_values(values):
    return u' '.join([unicode(value.get_python_value()) for value in values]) 

def get_string_from_efield4eobject(eobject, efield):
    if efield == None: return None
    # 做缓存
    cache_key = get_eobject_key(eobject, 'efield')
    dict_key = u"string_%d" % efield.pk
    eobject_dict = cache.get(cache_key)
    if eobject_dict == None:
        eobject_dict = {}
    if not eobject_dict.has_key(dict_key):
        eobject_dict[dict_key] = get_string_from_values(get_newest_value4efield(eobject, efield))
        cache.set(cache_key, eobject_dict, 1800)
    return eobject_dict[dict_key]

def get_string_from_key4eobject(eobject, key):
    cache_key = get_eobject_key(eobject, 'key')
    dict_key = key
    eobject_dict = cache.get(cache_key)
    if eobject_dict == None:
        eobject_dict = {}
    if not eobject_dict.has_key(dict_key):
        eobject_dict[dict_key] = get_string_from_values(get_newest_value4key(eobject, key))
        cache.set(cache_key, eobject_dict, 1800)
    return eobject_dict[dict_key]

def get_python_values4eobject(eobject, efield):
    # 做缓存
    key = get_eobject_key(eobject, 'python_values')
    dict_key = u"python_%d" % efield.pk
    eobject_dict = cache.get(key)
    if eobject_dict == None:
        eobject_dict = {}
    if not eobject_dict.has_key(dict_key):
        eobject_dict[dict_key] = list(get_newest_value4efield(eobject, efield))
        cache.set(key, eobject_dict, 1800)
    return eobject_dict[dict_key]

def clear_eobject_cache(eobject):
    for key in  [
        get_eobject_key(eobject, suffix = 'efield'),
        get_eobject_key(eobject, suffix = 'key'),
        get_eobject_key(eobject, suffix = 'python_values'),
        get_eobject_key(eobject, suffix = 'eform_dict_list_values'),
    ]:
        cache.delete(key)
    
# END    我们是 工具函数#}}}

from photologue.models import CommonImage #图片用这个
import validation
# 咱们是描述表单结构的！！
class EFormSet(models.Model):
    name = models.CharField(u"表单名称", max_length = 100)
    get_name_efield = models.ForeignKey("EField", blank = True, null = True)
    # 一些类似的字段
    image_efield = models.ForeignKey("EField", related_name = 'image4eformset', verbose_name = u'图片字段',  blank = True, null = True)
    category_efield = models.ForeignKey("EField", related_name = 'category4eformset', verbose_name = u'类别字段', blank = True, null = True)
    discription_efield = models.ForeignKey("EField", related_name = 'discription4eformset', verbose_name = u'描述信息的字段', blank = True, null = True)

    def get_first_available_eform(self, eobject):
        '''
            根据eobject 返回的一个合法的eform，
        '''
        for ei in EFormItem.objects.filter(eformset = self):
            eform = ei.get_eform(eobject)
            if eform != None:
                return eform
        return None

    def __unicode__(self):
        return self.name


class EFormItem(models.Model):
    KIND = (
        ('always_show', u"一直显示" ), # 这也意味着 这项是迟早要填的，如果此项不填， 是无法通过 is_complete 判断的
        ('show_on_conditions', u"需要填写才显示" ), # 这意味着 这项是根据需要才填写的， 如果不显示 就不用填写此项。
    )
    name = models.CharField(verbose_name = u'名称', max_length = 200)
    eformset = models.ForeignKey(EFormSet)
    weight = models.IntegerField(verbose_name = u'页面权重，大的在前', default = 1000)
    kind = models.CharField(verbose_name = u"类型", choices = KIND, max_length = 30, default = 'always_show')
    forms = models.ManyToManyField('EForm', verbose_name = u"包含的表单", null = True, blank = True)

    class Meta:
        ordering = ('-weight',)

    def __unicode__(self):
        return u"%s - %s - %s - %s" % (self.eformset, self.get_kind_display(), self.name,  self.weight)

    def get_eform(self, eobject):
        '''
            获得本 eformitem 实际对应的 eform
            返回None就说明没有一项通过验证了
        '''
        for eform in self.forms.all():
            if eform.test_logic_item(eobject):
                return eform
        return None

    def is_complete(self, eobject):
        '''
            显示单个 EFormItem 是否完成
        '''
        eform = self.get_eform(eobject)
        return eform != None and eform.is_complete(eobject)

    def get_next_eformitem(self):
        try:
            return self.eformset.eformitem_set.filter(Q(weight__lte = self.weight) & ~Q(pk = self.pk)).order_by('-weight')[0]
        except IndexError:
            return None

    def get_next_eform(self, eobject):
        eformitem = self
        while True:
            eformitem = eformitem.get_next_eformitem()
            if eformitem is None:
                return None
            eform = eformitem.get_eform(eobject)
            if eform is not None:
                return eform

        
class LogicItem(models.Model):
    """2type: LogicItem(efield=efield,text='test',compare='=');LogicItem(operator='and',logic=logicitem) """
    
    LOGINITEM_CHOICES = (
        ('=','equal'),
        ("!=",'notequal'),
        ('exists',u'填写过这个问题'),
        ('not_exists',u"没填写过这个问题"),
        ('not', '取反(logic中只要一个False就返回True)'),
    )
    LOGIC_CHOICES = (
        ('and','and'),
        ('or','or'), 
    )
    efield = models.ForeignKey("EField",null=True,blank=True)
    text = models.TextField(u"答案",null=True,blank=True)
    compare = models.CharField(choices=LOGINITEM_CHOICES,max_length=20,null=True,blank=True)
    operator = models.CharField(choices=LOGIC_CHOICES,max_length=20,null=True,blank=True)
    logic = models.ManyToManyField("self",null=True,blank=True, symmetrical=False)

    def pass_test(self,value_list):
        if self.operator =="and":
            for l in self.logic.all():
                if not l.pass_test(value_list=value_list):
                    return False
            return True
        if self.operator =="or":
            for l in self.logic.all():
                if l.pass_test(value_list=value_list):
                    return True
            return False
        if self.operator == "not":
            for l in self.logic.all():
                if not l.pass_test(value_list=value_list):
                    return True
            return False

        if value_list.filter(efield=self.efield).count()>0:
            value = value_list.filter(efield=self.efield)[0].value
            if (self.compare == "=" and self.text == value) or \
                (self.compare == "!=" and self.text != value) or \
                (self.compare == "exists" and value) or \
                (self.compare == "not_exists" and not value):
                return True
            return False
        return False

    def __unicode__(self):
        if self.compare:
            return "%s %s %s"%(unicode(self.efield),self.compare,self.text)
        elif self.operator == "not":
            return u"not(%s)" % u"".join([u"【%s】" % unicode(l) for l in self.logic.all()])
        elif self.operator:
            return  self.operator.join([u"【%s】" % unicode(l) for l in self.logic.all()])
        return "%d-%s"%(self.id,self.operator)


class EForm(models.Model):
    name = models.CharField(verbose_name = u'表单', max_length = 200)
    key = models.CharField(u'EForm的后台名称',max_length=200, blank=True, help_text = u'为了方便查找，最好唯一！！')
    repeat_n = models.IntegerField(verbose_name = u"答案可以重复的次数", default = 1)
    # TODO fileds 直接放在这里其实不好， 应该使用 throught， 然后在那个表里存放是是否能编辑 和排序的功能！！
    fields = models.ManyToManyField('EField', verbose_name = u"", null = True, blank = True)
    instruction = models.TextField(u'页面说明', blank = True)
    # required 本来想放在validation里的，因为涉及到了判断表单是否完善， 所以这里留了一份
    required = models.BooleanField(u'是否必填', default = True)
    logicitem = models.ForeignKey(LogicItem,null=True,blank=True)
    #TODO VALIDATION CLEAN 
    validation = models.CharField(verbose_name=u'页面级别表单认证,加后台逻辑,存函数名',max_length=100,null=True,blank=True,help_text=u"存在validation的文件里面") 

    def __unicode__(self):
        return u"(%d)%s[%s]" % (self.pk, self.name, self.key)

    def test_logic_item(self, eobject):
        # 测试针对 eobject的数据， 本 logic_item 是否通过
        if self.logicitem:
            value_list = Value.objects.filter(eobject=eobject)
            return self.logicitem.pass_test(value_list=value_list)
        return True

    def is_complete(self, eobject):
        values = Value.objects.filter(eobject = eobject, efield__eform = self)
        # 当还没有填写值的时候会返回None，这事就取0
        max_group = values.aggregate(Max('group'))['group__max'] or 0
        # return 填写过 and  需要填的field的数量 == 需要填写的field中 填写过的field的数量 (这代表都填写完了。)
        return values.filter(group = max_group).exists() and (self.fields.filter(required = True).count() == self.fields.filter(
            required = True,
            value__group = max_group,
            value__eobject = eobject,
        ).distinct().count())

    @cache_object_attr
    def get_eform_type(self):
        # EForm 的类型，特殊字段好特殊处理
        # TODO, 需要特殊方式展示的eform就在这里返回自己的类型,  目前只判断 image eform
        field_types = self.fields.all().values('field_type').distinct()
        if len(field_types) == 1 and field_types[0]['field_type'] == u'ImageField':
            return 'image'
        return 'normal'

class ExtraEFormEFiledConfig(models.Model):
    '''
        存储EForm中每个Field
        #TODO 1)  我觉得Field中的 widget 
        #TODO 2)  我觉得Field中的 weight 应该存储在 EForm EField 的关系中
        #TODO 3)  而EForm 到 EField 的manytomany 的关系也应该是 由本表来完成
    '''
    eform = models.ForeignKey('EForm')
    efield = models.ForeignKey('EField')
    is_locked = models.BooleanField(u'是否锁住(lock住后， 本字段只能查看，不能编辑)', default = False)

    class Meta:
        unique_together = ("eform", "efield")
    def __unicode__(self):
        return u'%s - %s' % (self.eform, self.efield,)

class Validator(models.Model):
    """
        django自带的函数有:validate_email,validate_slug,validate_ipv4_address[args都要为空]
        django自带的类有:RegexValidator,URLValidator,MaxValueValidator,MinValueValidator,MinLengthValidator,MaxLengthValidator
        自己写的要在validators文件里面:FileSizeValidator,FilePDFValidator,FileFlvValidator,FileNameValidator
    """
    """ for js_validator
    (1)required:true               必输字段
    (2)remote:"check.php"          使用ajax方法调用check.php验证输入值
    (3)email:true                  必须输入正确格式的电子邮件
    (4)url:true                    必须输入正确格式的网址
    (5)date:true                   必须输入正确格式的日期 日期校验ie6出错，慎用
    (6)dateISO:true                必须输入正确格式的日期(ISO)，例如：2009-06-23，1998/01/22 只验证格式，不验证有效性
    (7)number:true                 必须输入合法的数字(负数，小数)
    (8)digits:true                 必须输入整数
    (9)creditcard:                 必须输入合法的信用卡号
    (10)equalTo:"#field"           输入值必须和#field相同
    (11)accept:                    输入拥有合法后缀名的字符串（上传文件的后缀）
    (12)maxlength:5                输入长度最多是5的字符串(汉字算一个字符)
    (13)minlength:10               输入长度最小是10的字符串(汉字算一个字符)
    (14)rangelength:[5,10]         输入长度必须介于 5 和 10 之间的字符串")(汉字算一个字符)
    (15)range:[5,10]               输入值必须介于 5 和 10 之间
    (16)max:5                      输入值不能大于5
    (17)min:10                     输入值不能小于10
    """

    name = models.CharField(verbose_name=u"名字",max_length=100)
    validator = models.CharField(verbose_name=u"验证函数或者类",max_length=100)
    args = models.CharField(verbose_name=u"参数",max_length=100,null=True,blank=True,help_text=u"可以是正则表达式也可以是最大一个数字")
    message = models.CharField(verbose_name=u"出错信息",max_length=300,null=True,blank=True)
    js_validator = models.CharField(verbose_name=u"前台验证",max_length=500,null=True,blank=True,help_text=u"json dumps后的数据")

    def __unicode__(self):
        return self.name

    def get_js_validator(self):
        if self.js_validator:
            return simplejson.loads(self.js_validator)
        CONVERT_DJANGO_VALIDATOR_TO_VALIDATOR_DICT = {
            "validate_email":{"email":"true"},
            "URLValidator":{"url":"true"},
            "MaxValueValidator":{"max":self.args},
            "MinValueValidator":{"min":self.args},
            "MinLengthValidator":{"minlength":self.args},
            "MaxLengthValidator":{"maxlength":self.args},
            "validate_integer" : {"digits": "true"}
        }
        return CONVERT_DJANGO_VALIDATOR_TO_VALIDATOR_DICT.get(self.validator, None)

class EField(models.Model):
    # 注意：这里每加一个 field type 就必须同时维护下面的列表们
    FIELD_TYPE_CHOICES = (
        (u'CharField', u'字符串'),
        (u'TextField', u'文本框'),
        (u'ChoiceField', u'下拉框(普通)'),
        (u'MultipleChoiceField', u'多选框'),
        (u'SimpleModelChoiceField', u'下拉框(model)'),
        (u"ImageField",u"图片"),
        (u"VideoField",u"视频"),
        (u'FileField', u'文件'),
        (u"TagField",u"标签"),
        (u"DateField",u"日期"),
        (u"TimeField",u"时间"),
        (u"DateTimeField",u"日期-时间"),
        (u"RadioChoiceField",u"单选"),
    )

    MULT_CHOICES_FIELD = (
        u'MultipleChoiceField',
    )

    # 需要特别渲染来展示的字段
    SPECIAL_DISPLAY_FIELD = (
        u"ImageField",
        u"VideoField",
        u'FileField',
        u'TextField',
    )

    # 支持搜索的字段
    SUPPORT_SEARCH_FIELD = (
        u'CharField',
        u'ChoiceField',
        u'SimpleModelChoiceField',
        u'MultipleChoiceField',
        u"TagField",
    )

    # 以存储的方式存储 field
    VALUE_FIELD = (
        u'CharField', u'TextField', u'ChoiceField',  u'MultipleChoiceField', u'TagField', u'RadioChoiceField', u'DateTimeField', u'TimeField', u'DateTimeField',
    )
    CONTENT_TYPE_FIELD = (
        u'SimpleModelChoiceField', u"ImageField", 
    )
    VFILE_FIELD = (
        u"VideoField", u'FileField',
    )

    # 需要上传文件的Field， 方便对文件做特殊处理
    NEED_UPLOAD_FIELD = VFILE_FIELD + (
        u'ImageField',
    )

    # TODO weight 不应该耦合在 EField 里，这个应该写在 eform 里， 这个和 field无关，但是和form 的展现形式有关
    weight = models.IntegerField(verbose_name = u"问题权重，大的在前", default = 1000)
    key = models.CharField(verbose_name = u'字段的后台名称', max_length = 100)
    label = models.CharField(verbose_name = u"名称", max_length = 200)
    help_text = models.CharField(verbose_name = u"帮助信息", max_length = 200, blank = True)
    required = models.BooleanField(u'是否必填', default = True)
    # 掌管信息的类型
    field_type = models.CharField(verbose_name = u"EField的类型，存储CharField之类的东西", choices = FIELD_TYPE_CHOICES, max_length = 100)

    #TODO 专管信息的呈现
    #widget = models.ForeignKey(
    validator = models.ManyToManyField(Validator,null=True,blank=True)
    
    def get_db_value(self, python_value):
        # TODO...
        return python_value

    def get_python_value(self, content_object=None,vfile=None,db_value=None):
        # TODO datetime 没有实现 get_python_value方法， 修改后widget还得做一些修改
        if self.field_type in [u"VideoField",u'FileField']:
            return vfile
        elif self.field_type in ["ImageField","SimpleModelChoiceField"]:
            return content_object
        else:
            return db_value

    def get_validators(self):
        validators = self.validator.all()
        return validators

    def get_js_validator(self, initial_value = None):
        """for exmaple{validate:{required:true,maxlength:30}} """
        validators = self.get_validators()
        vs = {}
        for v in validators:
            if v.get_js_validator():
                vs.update(v.get_js_validator())
        if self.required and not (self.field_type in self.NEED_UPLOAD_FIELD and  initial_value != None):
            # 如果是一个 已经上传文件的 文件field 就没必要填写
            vs["required"] ="true"
        if len(vs)>0:
            val_str = "{validate:{"
            for k,v in vs.items():
                if val_str[-1] =="{":
                    val_str += "%s:%s"%(k,v)
                else:
                    val_str += ",%s:%s"%(k,v)
            val_str +="}}"
            return val_str
        return ""

    def __unicode__(self):
        return u"(%d)%s[%s]" % (self.pk, self.label, self.key)

    class Meta:
        ordering = ('-weight',)

class Choice(models.Model):
    key = models.CharField(u'选项的后台名称',max_length=200,blank=True)
    efield = models.ForeignKey(EField, related_name='choices')
    value = models.CharField(u'值', max_length=500)
    weight = models.IntegerField(u'权重', default = 1000)

    # 针对 
    content_type = models.ForeignKey(ContentType,null=True,blank=True, related_name = 'eform_choices')
    object_id = models.PositiveIntegerField(null=True,blank=True)
    content_object = generic.GenericForeignKey('content_type','object_id')

    def __unicode__(self):
        return self.value

    class Meta:
        ordering = ('-weight',)
    


# 洒家是真正存储表单内容的
class EObject(models.Model):
    '''
        一份表单的答案
    '''
    content_type = models.ForeignKey(ContentType, verbose_name= u"空疼忒泰普", related_name="state_object", blank=True, null=True)
    object_id = models.PositiveIntegerField(u"空疼忒爱帝", blank=True, null=True)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_id")
    
    default_fill_eformset = models.ForeignKey(EFormSet, verbose_name = u"填写方式", related_name = u'objects4fill', blank = True, null = True)
    default_display_eformset = models.ForeignKey(EFormSet, verbose_name = u"呈现方式", related_name = u'objects4display', blank = True, null = True)

    create_time = models.DateTimeField(auto_now_add = True)

    tags = TagField(u"标签",null=True,blank=True,help_text=u"标签")

    @cache_object_attr
    def __unicode__(self):
        return get_string_from_efield4eobject(self, self.default_display_eformset and self.default_display_eformset.get_name_efield) or u"还未填写名称"

    def is_complete(self, eformset = None):
        eformset = eformset or self.default_fill_eformset
        for eformitem in eformset.eformitem_set.all():
            eform = eformitem.get_eform(self)
            if eform == None:
                if eformitem.kind == 'always_show': return False
            else:
                if eform.required and not eform.is_complete(self):
                    return False
        return True

    def get_groups4eform(self, eform):
        return [v['group'] for v in Value.objects.filter(eobject = self, efield__eform = eform).order_by('group').values('group').distinct()]

    @cache_object_attr
    def get_image_object(self):
        if self.default_fill_eformset.image_efield:
            values = get_python_values4eobject(self,self.default_display_eformset.image_efield)
            return values[0].content_object if len(values) > 0 else None
        return None

    @cache_object_attr
    def get_category(self):
        if self.default_display_eformset.category_efield:
            return get_string_from_efield4eobject(self, self.default_display_eformset.category_efield)
        return None

    @cache_object_attr
    def get_discription(self):
        if self.default_display_eformset.discription_efield:
            return get_string_from_efield4eobject(self, self.default_display_eformset.discription_efield)
        return None

    @cache_object_attr
    def key_value_getter(self):
        '''
            key_value_getter 是一个对象， 你对它调用 ATTR 方法， 它就会到 本EObject 里找 key为 ATTR 的对象
            比如 eobject.key_value_getter.project_name,  就会去找 key为project_name 的 value
        '''
        class KeyValueGetter(object):
            def __init__(self, eobject):
                self.eobject = eobject
            def __getattr__(self, key):
                return  get_string_from_key4eobject(self.eobject, key)
        return KeyValueGetter(self)

    @cache_object_attr
    def eform_key_value_getter(self):
        '''
            key_value_getter 是一个对象， 你对它调用 ATTR 方法， 它就会到 本EObject 里找 key为 ATTR 的 EForm所有的 answer组
            比如 eobject.eform_key_value_getter.collaborator,  就会去找 key为 collaborator的 answer组
        '''
        from eform.utils import get_eform_value_dict_list
        class KeyValueGetter(object):
            def __init__(self, eobject):
                self.eobject = eobject
            def __getattr__(self, key):
                try:
                    eform = EForm.objects.get(key = key)
                except EForm.DoesNotExist:
                    return []
                return get_eform_value_dict_list(self.eobject, eform)
        return KeyValueGetter(self)
        

    def update_tags(self):
        """ 用于更新tag """
        te=EField.objects.filter(field_type="TagField",eform__eformitem__eformset = self.default_fill_eformset)
        if te.count>0:
            vs=Value.objects.filter(eobject=self,efield__in=te)
            for v in vs:
                if v.value:
                    self.tags = v.value
                    self.save()

    def is_blank(self):
        return not Value.objects.filter(eobject = self).exists()
    
    def clear_all_values(self):
        return Value.objects.filter(eobject = self).delete()

class Value(models.Model):
    eobject = models.ForeignKey(EObject)
    efield = models.ForeignKey(EField)
    value = models.TextField()
    group = models.IntegerField(verbose_name = u'答案分组，越早回答的分组越小')
    vfile = models.FileField(upload_to = get_file_path,null=True,blank=True, db_index = True)

    content_type = models.ForeignKey(ContentType,null=True,blank=True)
    object_id = models.PositiveIntegerField(null=True,blank=True)
    content_object = generic.GenericForeignKey('content_type','object_id')

    create_time = models.DateTimeField(auto_now_add = True)
    def __unicode__(self):
        return self.value

    def get_python_value(self):
        '''
            从数据库的文本转换为python值
        '''
        return self.efield.get_python_value(content_object = self.content_object,
                                            vfile = self.vfile,
                                            db_value = self.value)

## END 实现统计功能#{{{
class EObjFilterCondition(models.Model):
    # Field
    efield = models.ForeignKey(EField)
    # Value
    value = models.TextField()
    vfile = models.FileField(upload_to = get_file_path,null=True,blank=True, db_index = True)
    content_type = models.ForeignKey(ContentType,null=True,blank=True)
    object_id = models.PositiveIntegerField(null=True,blank=True)
    content_object = generic.GenericForeignKey('content_type','object_id')

    def get_python_value(self):
        return self.efield.get_python_value(content_object = self.content_object,
                                            vfile = self.vfile,
                                            db_value = self.value)
    def __unicode__(self):
        return u"%s - %s" % (self.efield, self.get_python_value())

class EObjStatistics(models.Model):
    name = models.CharField(u"名称", max_length=100, help_text = u'描述这是对什么的统计', blank = True)
    efilters = models.ManyToManyField(EObjFilterCondition,blank = True, null = True)

    def filter_eobjects(self, objs, prefix = 'eobject', extra_query = None):
        for eflt in self.efilters.all():
            query = Q(**{'%s__value__efield' %  prefix : eflt.efield})
            if extra_query: query = query & extra_query
            if eflt.efield.field_type in EField.VALUE_FIELD:
                query = query & Q(**{'%s__value__value' % prefix : eflt.value})
            if eflt.efield.field_type in EField.VFILE_FIELD:
                query = query & Q( **{"%s__value__vfile" % prefix : eflt.vfile})
            if eflt.efield.field_type in EField.CONTENT_TYPE_FIELD:
                query = query & Q(**{ "%s__value__content_type" % prefix : eflt.content_type}) & Q( **{u"%s__value__object_id" % prefix : eflt.object_id})
            objs = objs.filter(query)
        return objs
        
    def __unicode__(self):
        return self.name
## BEGIN 我们是为了实现 BaseActivity class 项目统计功能的#}}}
