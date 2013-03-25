# 1) pip install django-ckeditor

# 2) 设置 $REPO/settings.py
CKEDITOR_MEDIA_PREFIX = "/static/plugins/ckeditor/"
CKEDITOR_UPLOAD_PATH = os.path.join(MEDIA_ROOT, 'ckeditor_uploads/')
CKEDITOR_UPLOAD_PREFIX = os.path.join(MEDIA_URL, "ckeditor_uploads/")
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Mine', #  选择自己配置的 ckeditor 导航
        'height': 700,
        'width': 650,
        'language':'zh-cn',
        'pasteFromWordPromptCleanup':True, #Whether to prompt the user about the clean up of content being pasted from MS Word
    },

    'awesome_ckeditor': {
        'toolbar': 'Basic',
    },
}

# 3) 设置 $REPO/static/plugins/ckeditor/ckeditor/config.js
#    下面是一个精简的 导航栏，  带有上传文件的按钮
#    关于ckeditor 的配置和插件编写请参考 http://www.cnblogs.com/sonce/archive/2011/06/12/2078729.html
CKEDITOR.editorConfig = function( config )
{
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
    config.toolbar_Mine =
    [
        { name: 'styles',	items : [ 'PasteText','PasteFromWord','-','Undo','Redo','Find','Replace' , '-', 'Bold','Italic','Underline','Strike','Subscript','Superscript','-','RemoveFormat', 'Image','Flash','Table','HorizontalRule','SpecialChar','Iframe', 'Link','Unlink', 'UploadFiles', '-' , 'TextColor','BGColor'] },
        '/',
        { name: 'paragraph',	items : ['Source', 'NumberedList','BulletedList','Outdent','Indent','-','JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock', 'Styles','Format','Font','FontSize' ] }
    ];
    config.linkShowAdvancedTab = false;
    config.linkShowTargetTab = false;
    config.extraPlugins += (config.extraPlugins ? ',upload_files' : 'upload_files');
};

# 4) 下面是一个上传文件的插件，  /static/plugins/ckeditor/ckeditor/plugins/upload_files/plugin.js
CKEDITOR.plugins.add( 'upload_files',
{
	init : function( editor )
	{
		// Add the link and unlink buttons.
		editor.addCommand( 'upload_files', new CKEDITOR.dialogCommand( 'link' ) );
		editor.ui.addButton( 'UploadFiles',
			{
				label : "上传文件",//editor.lang.link.toolbar,
				command : 'upload_files',
                icon: this.path + 'images/upload.png'
			});
    }
})
# 5) 记得在/static/plugins/ckeditor/ckeditor/plugins/upload_files/images/upload.png 放置一个 16*16的 icon


#在form里如此使用
#BEGIN CKEDITOR
from ckeditor.widgets import CKEditorWidget
self.fields["XXX"].widget = CKEditorWidget()
#前台记得加 {{form.media}}
#END   CKEDITOR
