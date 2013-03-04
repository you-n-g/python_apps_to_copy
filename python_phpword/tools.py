#coding=utf8
import subprocess
import os
import uuid
import StringIO

php_code = '''
<?php
error_reporting(E_ALL);
if(php_sapi_name() == 'cli' && empty($_SERVER['REMOTE_ADDR'])) {
    define('EOL', PHP_EOL);
}
else {
    define('EOL', '<br />');
}
require_once 'phpcode/PHPWord.php';

// New Word Document
$PHPWord = new PHPWord();

// New portrait section
$document = $PHPWord->loadTemplate('templates/%s');
//setValue Code
%s
$document->save('%s');
echo "Done writing file" , EOL;
?>
'''

def replace(file_in,dic):
    words = ''
    for i,j in dic.items():
        words+="$document->setValue('%s',iconv('utf-8','gbk','%s'));\n"%(i,j)

    uid = uuid.uuid1().hex
    save_path = '/tmp/%s.docx'%uid
    php_template = php_code % (file_in,words,save_path)
    tmpfile = "phpcode/tmp_%s.php"%uid
    php_file = open(tmpfile,"w")

    php_file.write(php_template)
    php_file.close()
    try:
        result = subprocess.check_output(["php",tmpfile])
        #print result
    except subprocess.CalledProcessError:
        return None
    os.remove(tmpfile)
    file_out=file(save_path)
    output = file_out.read()
    os.remove(save_path)
    return output

#模板文件放入templates文件夹里面
#replace函数需要2个参数
#模板文件路径,替换字典
#调用函数返回的是一个docx文件read之后的结果，可以再保存到其他路径
#如下代码保存到当前目录的"sample.docx"
f = replace(
        "北京航空航天大学学生社团负责人任职承诺书.docx",
        {
        'name':'一起来唱歌',
        'master':'叶博',
        'sign':'林智鹏',
        'year':'2013',
        'month':'02',
        'day':'28',
        })

#print f
#print type(f)

#保存的文件名称
ff=open("sample.docx","w")
ff.write(f)
ff.close()
