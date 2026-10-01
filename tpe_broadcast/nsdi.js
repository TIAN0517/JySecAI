
var Nsdi = function() {
            "use strict";
            var $baseUrl = baseurl;
            let p = document.location.href.replace(baseurl, '').split('/');
            if(p[0] == 'manager'){
                $baseUrl += 'manager';
            }

            var varfilter = {}

            return {
                init: function() {
                    //toast
                    if(document.querySelector('.toast-container') == null){
                        $('body').append('<div class="toast-container position-fixed top-0 end-0 p-10"></div>');
                    }

                    //sidebar & minify
                    $('#sidebar li').removeClass('active');
                    if(document.querySelector('.sidebar-minify-btn') != null){
                        document.querySelector('.sidebar-minify-btn').addEventListener('click', function() {
                            $('#sidebar').data('minify', ($('#sidebar').data('minify') == 'Y')?'N':'Y');
                            $.ajax({
                                url: $baseUrl + '/main/api',
                                type: 'PATCH',
                                data:{'funcSwitch': 'minimal', 'status':$('#sidebar').data('minify')}
                            }).done(function(data){
                                if($('#sidebar').data('minify') == 'Y'){
                                    $('#page-container').addClass('page-sidebar-minified')
                                } else {
                                    $('#page-container').removeClass('page-sidebar-minified');
                                }
                            });
                        })
                    }

                    //checkbox line background color
                    if(document.querySelector('#checkall') != null){
                        document.querySelector('#checkall').addEventListener('click', function() {
                            let o = $(this), status = o.is(':checked');
                            o.closest('table').find('input[type=checkbox].checkbox').each(function(i){
                                if($(this).prop('disabled') == false){
                                    $(this).prop("checked",status);
                                    if(i % 2 == 1)
                                        $(this).closest('tr').children('td').css({'background-color' : (status)?'#ECEACC':''});
                                    else
                                        $(this).closest('tr').children('td').css({'background-color' : (status)?'#E2DFB4':''});
                                }
                            });
                        })
                    }
                    document.querySelectorAll('input[type="checkbox"].checkbox').forEach(function(e, i) {
                        e.addEventListener('click', function() {
                            let o = $(this), status = o.is(':checked');
                            if(i % 2 == 1)
                                o.closest('tr').children('td').css({'background-color' : (status)?'#ECEACC':''});
                            else
                                o.closest('tr').children('td').css({'background-color' : (status)?'#E2DFB4':''});
                        })
                    })

                    //inline editor
                    $('body').on('click','.editable',function(){
                        const container = $(this).closest('.inlineEditor'),
                              maxWidth = parseInt(container.closest('table').width() / container.closest('table').find('th').length);

                        let content = container.attr('data-content'),
                            width = container.data('width'),
                            verify = container.attr('data-verify'),
                            editor = container.attr('data-editor');
                            
                        content = Nsdi.htmlEncode(content);
                        if(width == undefined){
                            width = maxWidth;
                            if(width > 500){
                                width = '400px';
                            } else if(width > 80){
                                width += 'px';
                            } else {
                                width = '30%';
                            }
                        }
                        if(verify == undefined){
                            verify = '';
                        }
                        if(editor == undefined){
                            editor = '';
                        }
                        if(editor == 'textarea'){
                            container.html(`<div class="editablemodel d-flex">
                                <textarea class="form-control" style="width:${width}" data-verify="${verify}">${content}</textarea> 
                                <a class="btn btn-success btn-icon btn-circle btn-sm m-3" href="#" data-type="save">
                                    <i class="fa fa-check"></i>
                                </a> 
                                <a class="btn btn-danger btn-icon btn-circle btn-sm m-3" href="#" data-type="cancel">
                                    <i class="fa fa-times"></i>
                                </a>
                                </div>`);
                        } else {
                            content = Nsdi.escapeHtml(content);
                            container.html(`<div class="editablemodel d-flex">
                                <input type="text" value="${content}" class="form-control" style="width:${width}" data-verify="${verify}" /> 
                                <a class="btn btn-success btn-icon btn-circle btn-sm m-3" href="#" data-type="save">
                                    <i class="fa fa-check"></i>
                                </a> 
                                <a class="btn btn-danger btn-icon btn-circle btn-sm m-3" href="#" data-type="cancel">
                                    <i class="fa fa-times"></i>
                                </a>
                                </div>`);
                        }

                        return false;
                    })
                    $('body').on('click','.editablemodel > a',function(){
                        const container = $(this).closest('.inlineEditor'),
                              act    = $(this).attr('data-type'),
                              obj    = container.find('input');
                        let content  = container.attr('data-content'),
                              verify = obj.attr('data-verify');

                        container.find('.invalid-feedback').remove();
                        container.find('.is-invalid').removeClass('is-invalid');

                        if(act == 'save'){
                            if(verify == undefined){
                                verify = '';
                            }
                            if(verify != ''){
                                let vs = verify.split(' ');

                                if($.inArray('require', vs) != -1){
                                    if(obj.val() == ''){
                                        obj.addClass('is-invalid').attr('placeholder','必填');
                                        return false;
                                    }
                                }
                                if($.inArray('int', vs) != -1){
                                    if(Nsdi.isInt(obj.val()) == false){
                                        obj.addClass('is-invalid').attr('placeholder','填入半型數字').val('');
                                        return false;
                                    }
                                }
                                if($.inArray('string', vs) != -1){
                                    if(!isNaN(obj.val())){
                                        obj.addClass('is-invalid').attr('placeholder','填入文字').val('');
                                        return false;
                                    }
                                }
                            }
                        }
                        if(act == 'cancel'){
                            container.html('<a href="#" class="btn btn-sm btn-outline-secondary m-b-2 editable">'+content+'</a>');
                        }
                    })

                    //Loading animix
                    if(document.querySelector('#save') != null){
                        document.querySelector('#save').addEventListener('click', function() {
                            Nsdi.setLoadingAnimix(true);
                        })
                    }

                    //Filter Toolbar
                    $('[data-rowfilter]').change(function(){
                        const id = $(this).data('rowfilter'),
                              val = $(this).val();
                        varfilter[id] = encodeURIComponent(val);
                        Nsdi.setFilter()
                    })
                    $('[data-pagination-page]').click(function(){
                        varfilter['pages'] = $(this).data('pagination-page');
                        Nsdi.setFilter();
                    });

                    $('#keysearch').keypress(function(e) {
                        if(e.which == 13) {
                            varfilter['search'] = encodeURIComponent($('#keysearch').val());
                            varfilter['pages'] = 1;
                            Nsdi.setFilter();
                            return false;
                        }
                    });
                    $('#keysearchbutton').click(function(){
                        varfilter['search'] = encodeURIComponent($('#keysearch').val());
                        varfilter['pages'] = 1;
                        Nsdi.setFilter();
                    });
                    $('#toolbar-form').on('click', '#search-clear-button', function(){
                        varfilter['search'] = encodeURIComponent('');
                        varfilter['pages'] = 1;
                        Nsdi.setFilter();
                    });

                },
                isInt: function(number) {
                    if(isNaN(number)){
                        return false;
                    } else {
                        let val = parseFloat(number)
                        if(Number.isInteger(val) == false){
                            return false;
                        }
                    }
                    return true;
                },
                setToast: function(msg) {
                    const container = document.querySelector('.toast-container');
                    let content = document.createElement('div');
                    content.innerHTML = '<div class="d-flex">' +
                                '<div class="toast-body w-100">' + msg + '</div>' +
                                '<button type="button" class="btn-close m-t-10 m-r-10" data-bs-dismiss="toast" aria-label="Close"></button>' +
                            '</div>';
                    content.setAttribute('role',"alert");
                    content.setAttribute('aria-live',"assertive");
                    content.setAttribute('aria-atomic',"true");
                    content.classList.add('toast','text-dark','bg-gradient-orange','align-items-center');
                    container.appendChild(content);
                    container.style.zIndex = 9999;

                    let obj = container.querySelector('.toast:last-child');
                    let toast = new bootstrap.Toast(obj)
                    toast.show();
                    obj.addEventListener('hidden.bs.toast', function () {
                        this.remove()
                    })
                },
                setLang: function(lang) {
                    $.ajax({
                        url: $baseUrl + '/main/api',
                        type: 'PATCH',
                        data:{'funcSwitch': 'lang', 'lang':lang}
                    }).done(function(data){
                        if(data.status == 'success'){
                            window.location.reload();
                        }
                    });
                },
                keepOnline: function() {
                    $.ajax({
                        url: $baseUrl + '/online/api',
                        type: 'POST',
                    }).done(function(data){
                        if(data.status == 'error'){
                            // window.location = $baseUrl + '/logout";
                        }
                    });
                },
                sidebar: function(id) {
                    $('.has-sub[data-code="' + id + '"]').addClass('active');
                },
                minify: function() {
                    if($('#sidebar').data('minify') == 'Y'){
                        $('#page-container').addClass('page-sidebar-minified')
                    } else {
                        $('#page-container').removeClass('page-sidebar-minified');
                    }
                },
                //inline editor
                htmlEncode: function(value) {
                    // 建立一個暫存的div元素，並使用text()將內容存成html編碼文字後再用html()取出
                    return $('<div/>').text(value).html();
                },     
                escapeHtml: function(text) {
                    const map = {
                        '&': '&amp;',
                        '<': '&lt;',
                        '>': '&gt;',
                        '"': '&quot;',
                        "'": '&#039;'
                    };

                    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
                },
                setLoadingAnimix: function(status){
                    $('body').find('#sysloading').remove();

                    if(status == true){
                        $('body').append('<div id="sysloading" style="position:absolute;width:100%;bottom:0;top:50%;margin:auto;z-index:99999" class="text-center"><i class="fa fa-sync fa-spin fa-3x fa-fw"></i><h3>處理中,請稍後...</h3></div>');
                        
                        var timer = setInterval(function(){
                            if($('.invalid-feedback').length > 0){
                                $('body').find('#sysloading').remove();
                                clearInterval(timer);

                                $('html').animate({
                                        scrollTop: $('.invalid-feedback:eq(0)').offset().top-300
                                    }, 1000,'linear');
                            }
                        },1);
                    }
                },
                numberWithCommas: function(x) {//數字千分位逗點
                    if(x == 0) return x;
                    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                },
                paddingLeft: function(str, length) {//左邊補0
                    if(String(str).length >= length)
                        return str;
                    else
                        return paddingLeft("0" +str,length);
                },
                FileIcon: function(file) {
                    let filetype = file.split('.'), img;
                    switch(filetype[filetype.length-1].toLowerCase()){
                        case 'jpg':
                        case 'jpeg':
                        case 'gif':
                        case 'png':
                            img = "assets/manager/icon/attachment-icon/images.png";
                        break;
                        case 'xls':
                        case 'xlsx':
                            img = "assets/manager/icon/attachment-icon/xls.png";
                            break;
                        case 'pdf':
                            img = "assets/manager/icon/attachment-icon/pdf.png";
                            break;
                        case 'ppt':
                        case 'pptx':
                            img = "assets/manager/icon/attachment-icon/ppt.png";
                            break;
                        case 'doc':
                        case 'docx':
                        case 'odt':
                            img = "assets/manager/icon/attachment-icon/word.png";
                            break;
                        case 'zip':
                            img = "assets/manager/icon/attachment-icon/zip.png";
                            break;
                        default:
                            img = "assets/manager/icon/attachment-icon/others.png";
                            break;
                    }
                    return img;
                },

                getVideo: function(url) {
                    let info = {
                                    'type'     : 'Unknown',
                                    'url'      : url,
                                    'id'       : '',
                                    'thumbnail': '',
                                    'embed_url': ''
                                }

                    if(url != ''){
                        //Youtube
                        if (url.indexOf('youtube') > 0 || url.indexOf('youtu.be') > 0) {
                            if(url.match(/v=([^&]+)/) != null){
                                let videoID = url.match(/v=([^&]+)/)[1];

                                info.type      = 'Youtube';
                                info.id        = videoID;
                                info.thumbnail = 'https://img.youtube.com/vi/'+videoID+'/hqdefault.jpg';
                                info.embed_url = 'https://www.youtube.com/embed/' + videoID;

                                // return info;
                                /*
                                if want to check img exist, please do below code after return
                                $("<img>").attr('src', info.thumbnail)
                                .on("error", function(e) {
                                    console.log(e.type,this.src)
                                })
                                .on("load", function(e) {
                                    console.log(e.type,this.src)
                                })
                                */
                            }
                        }

                        //Vimeo
                        else if (url.indexOf('vimeo') > 0) {
                            if(url.match(/(?:vimeo)\.com.*(?:videos|video|channels|)\/([\d]+)/i) != null){
                                $.ajax({
                                    url: 'https://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/' + url.match(/(?:vimeo)\.com.*(?:videos|video|channels|)\/([\d]+)/i)[1],
                                    type: 'GET',
                                    async: false,
                                }).done(function(data){
                                    if(data.video_id != undefined){
                                        info.type      = 'Vimeo';
                                        info.id        = data.video_id;
                                        info.thumbnail = data.thumbnail_url;
                                        info.embed_url = 'https://player.vimeo.com/video/' + data.video_id + '?badge=0';
                                    }
                                })
                            }
                        }

                        //Dailymotion
                        else if (url.indexOf('dailymotion') > 0 || url.indexOf('dai.ly') > 0) {
                            if(url.match(/(?:dailymotion)\.com.*(?:videos|video|channels|)\/([^&]+)/i) != null){
                                let videoID = url.match(/(?:dailymotion)\.com.*(?:videos|video|channels|)\/([^&]+)/i)[1];
                                info.type      = 'Dailymotion';
                                info.id        = videoID;
                                info.thumbnail = 'https://www.dailymotion.com/thumbnail/video/' + videoID;
                                info.embed_url = 'https://www.dailymotion.com/embed/video/' + videoID;
                            }
                        }
                    }
                    return info;
                },
                base64toBlob: function(base64Data) {
                    const b64toBlob = (b64Data, contentType='', sliceSize=512) => {
                        const byteCharacters = atob(b64Data);
                        const byteArrays = [];

                        for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
                            const slice = byteCharacters.slice(offset, offset + sliceSize);

                            const byteNumbers = new Array(slice.length);
                            for (let i = 0; i < slice.length; i++) {
                                byteNumbers[i] = slice.charCodeAt(i);
                            }

                            const byteArray = new Uint8Array(byteNumbers);
                            byteArrays.push(byteArray);
                        }

                        const blob = new Blob(byteArrays, {type: contentType});
                        return blob;
                    }

                    const BASE64_MARKER = ';base64,';
                    const parts = base64Data.split(BASE64_MARKER);
                    const contentType = parts[0].split(':')[1];
                    const blob = b64toBlob(parts[1], contentType);

                    return blob;
                    /*
                    example:
                    const blobUrl = URL.createObjectURL(blob);
                    const img = document.createElement('img');
                    img.src = blobUrl;
                    document.body.appendChild(img);

                    Or 
                    const blobUrl = URL.createObjectURL(blob);
                    var objbuilder = '';
                    objbuilder += ('<object width="100%" height="100%" data="');
                    objbuilder += (blobUrl);
                    objbuilder += ('" type="application/pdf" class="internal">');
                    objbuilder += ('<embed src="');
                    objbuilder += (blobUrl);
                    objbuilder += ('" type="application/pdf"  />');
                    objbuilder += ('</object>');

                    var win = window.open("#","_blank");
                    var title = "my tab title";
                    win.document.write('<html><title>'+ title +'</title><body style="margin-top: 0px; margin-left: 0px; margin-right: 0px; margin-bottom: 0px;">');
                    win.document.write(objbuilder);
                    win.document.write('</body></html>');
                    layer = jQuery(win.document);
                    */
                },
                dateVerify: function(date, format) {
                    format = format || 'YYYY-MM-DD';
                    let status = moment(date, format,true).isValid(), f, d;
                    if(status){
                        if(format.indexOf('/') != -1){
                            f = format.split('/');
                            d = date.split('/');
                        } else if(format.indexOf('-') != -1){
                            f = format.split('-');
                            d = date.split('-');
                        }
                        if(f[0] == 'YYYY'){
                            if(parseInt(d[0]) < 1970){
                                return false;
                            } else {
                                return true;
                            }
                        }
                        return status; 
                    } else {
                        return false; 
                    }
                },
                handelfilter: function(datas) {
                    $.each(datas, function(k, v){
                        if(typeof(v) == 'string'){
                            datas[k] = encodeURIComponent(v)
                        }
                        if($('[data-rowfilter='+k+']').length > 0){
                            let obj = $('[data-rowfilter='+k+']');
                            switch(obj.prop('tagName')){
                                case 'SELECT':
                                case 'INPUT':
                                    obj.val(v);
                                break;
                            }
                        }
                        if(k == 'search'){
                            if(v != ''){
                                $('#keysearchbutton').before('<button class="btn btn-danger" type="button" id="search-clear-button"><i class="fa fa-times"></i></button>');
                            }
                        }
                    });

                    varfilter = datas;
                },
                setFilter: function(){
                    window.location = '?filter='+btoa(JSON.stringify(varfilter));
                },
                get_data: function() {
                    return varfilter;
                }


            }
    }();

Nsdi.init();

var NsdiProducts = function() {
            "use strict";
            var $baseUrl = baseurl;
            let p = document.location.href.replace(baseurl, '').split('/');
            if(p[0] == 'manager'){
                $baseUrl += 'manager';
            }
            var _csrf = {};
            var config = {
                            'multi': true,
                        };
            var get_products_list_opt = {
                                        'page'    : 1,
                                        'filter'  : {
                                                        menu    : '',
                                                        nav     : '',
                                                        code    : '',
                                                        title   : '',
                                                        status  : ''
                                                    },
                                        'menu'    : [],
                                        'submenu' : [],
                                        'items'   : {},
                                        'eof'     : 0
                                    };


            return {
                init: function(csrf) {
                    get_products_list_opt[csrf.name] = csrf.data;
                    _csrf = csrf;

                    if(document.querySelector('#products-modal-dialog') == null){
                        $('body').append(`
                        <div class="modal fade" id="products-modal-dialog" data-bs-focus="false">
                            <div class="modal-dialog modal-xl">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h4 class="modal-title">從下列選單勾選商品</h4>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-hidden="true"></button>
                                    </div>
                                    <div class="modal-body">
                                        <div class="table-responsive" id="listtable" style="max-height:600px;overflow: auto">
                                        <table class="table table-striped table-bordered nowrap table-hover" width="100%">
                                            <thead>
                                                <tr>
                                                    <th data-eje-selector>
                                                        勾選
                                                    </th>
                                                    <th>
                                                        <button type="button" class="btn btn-xs btn-successr p-5 advance" data-toggle="popover" data-filter="menu"><i class="fa fa-magic"></i> 類型</button>
                                                    </th>
                                                    <th>
                                                        <button type="button" class="btn btn-xs btn-successr p-5 advance" data-toggle="popover" data-filter="nav"><i class="fa fa-magic"></i> 選單</button>
                                                    </th>
                                                    <th>
                                                        <button type="button" class="btn btn-xs btn-successr p-5 advance" data-toggle="popover" data-filter="code"><i class="fa fa-magic"></i> 貨號</button>
                                                    </th>
                                                    <th>
                                                        <button type="button" class="btn btn-xs btn-successr p-5 advance" data-toggle="popover" data-filter="title"><i class="fa fa-magic"></i> 商品名稱</button>
                                                    </th>
                                                    <th>
                                                        <button type="button" class="btn btn-xs btn-successr p-5 advance" data-toggle="popover" data-filter="status"><i class="fa fa-magic"></i> 顯示狀態</button>
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                            </tbody>
                                        </table>
                                        </div>

                                    </div>
                                    <div class="modal-footer justify-content-between">
                                        <div>共 <span id="matchamout">0</span> 筆資料符合</div>
                                        <div>
                                            <a href="javascript:;" class="btn btn-sm btn-outline-secondary cls" data-bs-dismiss="modal">關閉</a>
                                            <a href="javascript:;" class="btn btn-sm btn-success done" data-bs-dismiss="modal">確定</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>`);
                    }

                    $('#products-modal-dialog').on('show.bs.modal', function (event) {
                        let options = [];
                        let button = $(event.relatedTarget)
                        options = button.data();

                        NsdiProducts.get_products_list();

                        $('#products-modal-dialog').find('.modal-footer').find('.products-modal-options').remove();
                        $('#products-modal-dialog').find('.modal-footer').append('<div class="products-modal-options" style="display:none">'+JSON.stringify(options)+'</div>');
                    })

                    $('#products-modal-dialog').find('#listtable').scroll(function(){
                        let position = $('#products-modal-dialog').find('tbody').find('tr:last').position(),
                            offset = $('#products-modal-dialog').find('tbody').find('tr:last').offset();
                        if(offset.top <= (position.top-500)){
                           get_products_list_opt.page += 1;
                           NsdiProducts.get_products_list();
                        }
                    })

                    //filter func
                    $('.advance[data-filter=menu]').popover({
                        html: true,
                        placement: 'top',
                        title: '篩選項目',
                        sanitize: false,
                        content: function(){
                                        let nav = '';
                                        $.each(get_products_list_opt.menu, function( index, value ) {
                                            nav += '<div class="row m-5"><label><input type="checkbox" class="form-check-input eje-products-list" data-filter="menu" value="'+index+'" > '+value+'</label></div>';
                                        })
                                        return nav;
                                    }
                    })
                    $('.advance[data-filter=nav]').popover({
                        html: true,
                        placement: 'top',
                        title: '篩選項目',
                        sanitize: false,
                        content: function(){
                                        let nav = '';
                                        $.each(get_products_list_opt.submenu, function( index, value ) {
                                            nav += '<div class="row m-5"><label><input type="checkbox" class="form-check-input eje-products-list" data-filter="nav" value="'+index+'" > '+value+'</label></div>';
                                        })
                                        return nav;
                                    }
                    })
                    $('.advance[data-filter=code]').popover({
                        html: true,
                        placement: 'top',
                        title: '篩選項目',
                        sanitize: false,
                        content: '<label>關鍵字: <input type="text" class="eje-products-string" data-filter="code" ></label>'
                    })
                    $('.advance[data-filter=title]').popover({
                        html: true,
                        placement: 'top',
                        title: '篩選項目',
                        sanitize: false,
                        content: '<label>關鍵字: <input type="text" class="eje-products-string" data-filter="title" ></label>'
                    })
                    $('.advance[data-filter=status]').popover({
                        html: true,
                        placement: 'top',
                        title: '篩選項目',
                        sanitize: false,
                        content: function(){
                                        return '<div class="row m-5"><label><input type="checkbox" class="form-check-input eje-products-list" data-filter="status" value="Y" > 顯示</label></div><div class="row m-5"><label><input type="checkbox" class="form-check-input eje-products-list" data-filter="status" value="N" > 隱藏</label></div>';
                                    }
                    })
                    $('.advance').on('shown.bs.popover', function () {
                        $('.popover-body').css({
                            'font-size':'12px'
                            });
                        let type = $(this).attr('data-filter'), i;
                        if(type == 'menu' && get_products_list_opt.filter.menu != ''){
                            let item = get_products_list_opt.filter.menu.split(',');
                            for(i=0;i<item.length;i++){
                                $('.popover-body').find('input[data-filter=menu]').each(function(){
                                    if($(this).val() == item[i]){
                                        $(this).prop('checked',true);
                                    }
                                })
                            }
                        }
                        if(type == 'nav' && get_products_list_opt.filter.nav != ''){
                            let item = get_products_list_opt.filter.nav.split(',');
                            for(i=0;i<item.length;i++){
                                $('.popover-body').find('input[data-filter=nav]').each(function(){
                                    if($(this).val() == item[i]){
                                        $(this).prop('checked',true);
                                    }
                                })
                            }
                        }
                        if(type == 'code' && get_products_list_opt.filter.code != ''){
                            $('.popover-body').find('input[data-filter=code]').val(get_products_list_opt.filter.code);
                        }
                        if(type == 'title' && get_products_list_opt.filter.title != ''){
                            $('.popover-body').find('input[data-filter=title]').val(get_products_list_opt.filter.title);
                        }
                        if(type == 'status' && get_products_list_opt.filter.status != ''){
                            let item = get_products_list_opt.filter.status.split(',');
                            for(i=0;i<item.length;i++){
                                $('.popover-body').find('input[data-filter=status]').each(function(){
                                    if($(this).val() == item[i]){
                                        $(this).prop('checked',true);
                                    }
                                })
                            }
                        }
                    })
                    $('body').on('click', '.eje-products-list', function(){
                        let type = $(this).data('filter');
                        switch(type){
                            case 'menu':
                                let menu = [];
                                $(this).closest('.popover-body').find('input').each(function(){
                                    if($(this).is(':checked')){
                                        menu.push($(this).val());
                                    }
                                })
                                if(menu.length > 0){
                                    get_products_list_opt.filter.menu = menu.join(',');
                                } else {
                                    get_products_list_opt.filter.menu = '';
                                }
                            break;
                            case 'nav':
                                let nav = [];
                                $(this).closest('.popover-body').find('input').each(function(){
                                    if($(this).is(':checked')){
                                        nav.push($(this).val());
                                    }
                                })
                                if(nav.length > 0){
                                    get_products_list_opt.filter.nav = nav.join(',');
                                } else {
                                    get_products_list_opt.filter.nav = '';
                                }
                            break;
                            case 'title':
                            break;
                            case 'status':
                                let status = [];
                                $(this).closest('.popover-body').find('input').each(function(){
                                    if($(this).is(':checked')){
                                        status.push($(this).val());
                                    }
                                })
                                if(status.length > 0){
                                    get_products_list_opt.filter.status = status.join(',');
                                } else {
                                    get_products_list_opt.filter.status = '';
                                }
                            break;
                        }
                        get_products_list_opt.eof  = 0;
                        get_products_list_opt.page = 1;
                        NsdiProducts.get_products_list()
                    })
                    .on('keyup', '.eje-products-string', function(){
                        let type = $(this).data('filter');
                        switch(type){
                            case 'menu':
                            break;
                            case 'nav':
                            break;
                            case 'code':
                                get_products_list_opt.filter.code = $(this).val();
                            break;
                            case 'title':
                                get_products_list_opt.filter.title = $(this).val();
                            break;
                        }
                        get_products_list_opt.page = 1;
                        NsdiProducts.get_products_list()
                    })
                    .on('click', '.eje-products-list-item', function(){
                        const code = $(this).val(),
                              title= $(this).closest('tr').find('td[data-tag="title"]').text().trim();

                        if(get_products_list_opt.items[code] == undefined){
                            get_products_list_opt.items[code] = title;
                        } else {
                            delete get_products_list_opt.items[code]
                        }
                        /*
                        let code = $(this).val(), idx = $.inArray(code, get_products_list_opt.items);
                        if(idx == -1){
                            //add
                            get_products_list_opt.items.push(code);
                        } else {
                            //remove
                            get_products_list_opt.items.splice(idx, 1);
                        }
                        */
                    });
                },
                setConfig: function(options) {
                    config = Object.assign(config, options);
                },
                setSelectorAll: function() {
                    if(config.multi){
                        $('#products-modal-dialog').find('[data-eje-selector]').html(`<input class="form-check-input" type="checkbox" value="" id="selectorAllproducts">
                                                            <label class="form-check-label" for="selectorAllproducts">全選</label>`);
                        $('#products-modal-dialog').find('input[type="radio"]').attr('type','checkbox').attr('name','check[]');

                        document.querySelector('#selectorAllproducts').addEventListener('click', function(e) {
                            console.log(1)
                            if($('#selectorAllproducts').is(':checked')){
                                $('#products-modal-dialog').find('.eje-products-list-item').each(function(){
                                    $(this).prop('checked', true);

                                    let code = $(this).val(),
                                        title= $(this).closest('tr').find('td[data-tag="title"]').text().trim();

                                    if(get_products_list_opt.items[code] == undefined){
                                        get_products_list_opt.items[code] = title;
                                    }
                                })
                            } else {
                                $('#products-modal-dialog').find('.eje-products-list-item').each(function(){
                                    $(this).prop('checked', false);

                                    let code = $(this).val(),
                                        title= $(this).closest('tr').find('td[data-tag="title"]').text().trim();

                                    if(get_products_list_opt.items[code] != undefined){
                                        delete get_products_list_opt.items[code]
                                    }
                                })
                            }
                        })
                    } else {
                        $('#products-modal-dialog').find('[data-eje-selector]').html(`勾選`);
                        $('#products-modal-dialog').find('input[type="checkbox"]').attr('type','radio').attr('name','product');
                    }
                },
                get_products_list: function(){
                    // console.log(get_products_list_opt);
                    if(get_products_list_opt.eof == 1){
                        return false;
                    }
                    $.ajax({
                        url: $baseUrl + '/products/getproducts/api',
                        type: 'POST',
                        data: get_products_list_opt
                    }).done(function(data){
                        if(data.status == 'success'){
                            let html = '', amount = data.msg.products.length;

                            if(amount == 0){
                                get_products_list_opt.page -= 1;
                                get_products_list_opt.eof = 1;
                                return false;
                            }

                            for(let i=0;i<amount;i++){
                                let item = data.msg.products[i];
                                let menu = '', nav = [];

                                for(let j=0;j<item.nav.length;j++){
                                    nav.push(item.nav[j].title)
                                    menu = item.nav[j].parent.title;
                                }

                                html += '<tr>';
                                if(get_products_list_opt.items[item.pmcode] != undefined){
                                    html += '<td><input type="checkbox" name="check[]" class="form-check-input checkbox eje-products-list-item" checked value="'+item.pmcode+'" ></td>';
                                } else {
                                    html += '<td><input type="checkbox" name="check[]" class="form-check-input checkbox eje-products-list-item" value="'+item.pmcode+'" ></td>';
                                }
                                html += '<td data-tag="menu">'+menu+'</td>';
                                html += '<td data-tag="nav">'+nav.join(', ')+'</td>';
                                html += '<td data-tag="pmcode">'+item.pmcode+'</td>';
                                html += '<td data-tag="title">'+item.title+'</td>';
                                if(item.status == 'Y')
                                    html += '<td><span class="badge bg-success">顯示</span></td>';
                                else
                                    html += '<td><span class="badge bg-danger">隱藏</span></td>';
                                html += '</tr>';
                            }

                            if(get_products_list_opt.page <= 1)
                                $('#products-modal-dialog').find('tbody').html(html);
                            else
                                $('#products-modal-dialog').find('tbody').append(html);

                            $('#products-modal-dialog').find('#matchamout').text(data.msg.amount); 
                            get_products_list_opt.menu    = data.msg.menu;
                            get_products_list_opt.submenu = data.msg.submenu;

                            if(config.multi){
                                $('#products-modal-dialog').find('input[type="radio"]').attr('type','checkbox').attr('name','check[]');
                            } else {
                                $('#products-modal-dialog').find('input[type="checkbox"]').attr('type','radio').attr('name','product');
                            }
                        }
                    });
                },
                get_product: function(id, cb) {
                    let formdata = {
                                    'funcSwitch': 'product',
                                    'id'        : id,
                        }
                    formdata[_csrf.name] = _csrf.data;

                    $.ajax({
                        url: $baseUrl + '/products/getproducts/api',
                        type: 'POST',
                        data: formdata
                    }).done(cb);

                    /* how to use:
                    NsdiProducts.get_product('xxxxx', function(data) {
                        if(data.status == 'error'){
                            return false;
                        }

                        if(data.msg == 'Y'){
                        }
                    });
                    */
                },
                get_spec: function(id, cb) {
                    let formdata = {
                                    'funcSwitch': 'details',
                                    'id'        : id,
                        }
                    formdata[_csrf.name] = _csrf.data;

                    $.ajax({
                        url: $baseUrl + '/products/getproducts/api',
                        type: 'POST',
                        data: formdata
                    }).done(cb);

                    /* how to use:
                    NsdiProducts.get_product('xxxxx', function(data) {
                        if(data.status == 'error'){
                            return false;
                        }

                        if(data.msg == 'Y'){
                        }
                    });
                    */
                },
                get_data: function() {
                    return get_products_list_opt;
                }
            }
    }();
