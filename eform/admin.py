#coding= utf8
from models import EFormSet, EFormItem, EForm, EField, Choice, EObject, Value,Validator,LogicItem, ExtraEFormEFiledConfig, EObjFilterCondition, EObjStatistics
from django.contrib import admin

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1
    fields = ('value', 'weight', 'key', 'content_type', 'object_id')

class ValidatorInline(admin.TabularInline):
    model = EField.validator.through

class FieldAdmin(admin.ModelAdmin):
    list_select_related = True
    list_filter = ('eform',)
    list_display_links = ('pk',)
    list_display = ('pk', 'label', 'key', 'field_type', 'help_text', 'weight', 'required')
    inlines = [
        ChoiceInline,
    ]
    ordering = ['-weight']
    list_editable = ('label', 'key', 'field_type', 'help_text', 'weight', 'required')


class EFormOrderInline(admin.TabularInline):
    model = EFormItem
    extra = 0
    
class EFormSetAdmin(admin.ModelAdmin):
    inlines = [
        EFormOrderInline,
    ]

class ValueAdmin(admin.ModelAdmin):
    list_display = ('efield','value',)
    search_fields = ('value',)
    list_filter = ('efield','eobject')

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('efield','value',)
    search_fields = ('value',)
    list_filter = ('efield',)

class EFormAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name','repeat_n', 'instruction', 'fields')
    list_editable = ('name','repeat_n', 'instruction', 'fields')

class EFormOrderAdmin(admin.ModelAdmin):
    list_display = ('pk','eformset', 'weight', 'kind')
    list_editable = ('eformset', 'weight', 'kind')
    ordering = ['-weight']

class EObjectAdmin(admin.ModelAdmin):
    list_display = ('pk', 'default_fill_eformset', 'default_display_eformset' ,'content_type', 'object_id',)
    list_editable = ('default_fill_eformset', 'default_display_eformset' ,'content_type', 'object_id',)

class ValidatorAdmin(admin.ModelAdmin):
    pass

class LogicItemAdmin(admin.ModelAdmin):
    pass

class ExtraEFormEFiledConfigAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_locked',)
    list_editable = ('is_locked',)

admin.site.register(EField, FieldAdmin)
admin.site.register(EFormSet, EFormSetAdmin)
admin.site.register(Value, ValueAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(EForm, EFormAdmin)
admin.site.register(EFormItem, EFormOrderAdmin)
admin.site.register(EObject, EObjectAdmin)
admin.site.register(Validator, ValidatorAdmin)
admin.site.register(LogicItem, LogicItemAdmin)
admin.site.register(ExtraEFormEFiledConfig, ExtraEFormEFiledConfigAdmin)
admin.site.register(EObjFilterCondition)
admin.site.register(EObjStatistics)
