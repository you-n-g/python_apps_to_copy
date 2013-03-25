#!/usr/bin/env python
#-*- coding:utf8 -*-
from django.core.validators import validate_email,validate_slug,validate_ipv4_address,RegexValidator,URLValidator,MaxValueValidator,MinValueValidator,MinLengthValidator,MaxLengthValidator, validate_integer
from tools.utils import get_file_type
from django.core.exceptions import ValidationError

class FileSizeValidator(object):
    message = u"文件太大，最大只能上传%sM文件"
    code = "max_size"

    def __init__(self,max_size=100*1024*1024):#100M
        self.max_size = max_size

    def __call__(self,value):
        if value.size>self.max_size*1024*1024:
            raise ValidationError(
                self.message % self.max_size,
                code=self.code,
            )

class FileTypeBaseValidator(object):
    """目前只识别flv和pdf格式 [python magic]"""
    FILE_TYPE_CHOICES = {"pdf":"application/pdf","flv":"video/x-flv"}
    message = u"文件格式错误,需上传%s格式文件"
    code ="file type error"
    filetype= ""

    def __init__(self,*args):
        pass

    def __call__(self,value):
        file_type = get_file_type(value)
        if not file_type == self.FILE_TYPE_CHOICES[self.filetype]:
            raise ValidationError(
                self.message %self.filetype,
                code=self.code,
            )

class FilePDFValidator(FileTypeBaseValidator):
    """pdf格式"""
    filetype="pdf"

class FileFlvValidator(FileTypeBaseValidator):
    """flv格式"""
    filetype = "flv"

class FileNameValidator(object):
    """ 
        file后缀名，多个用|隔开
        大小写不敏感
    """
    message = u"文件格式有误，只能是%s的文件"
    code = "file type error"

    def __init__(self,file_name):
        self.file_name = file_name
        self.name_list = [name.lower() for name in self.file_name.split("|")]
    def __call__(self,value):
        name = value.name.split(".")[-1]
        if not (name.lower() in self.name_list):
            raise ValidationError(
                self.message %self.file_name,
                code = self.code,
                )

class MutiLimitValidator(object):
    '''
        对多选项的字段进行数量限制
    '''
    message = u"最多只能选择%d项"
    def __init__(self, limit):
        self.limit = int(limit)
    def __call__(self, value):
        if len(value)  >  self.limit:
            raise ValidationError(
                self.message % self.limit,
            )
