$(document).ready(function () {
	toastr.options = {
		"closeButton": false,               // 顯示關閉按鈕
		"debug": false,                     // 除錯
		"newestOnTop": true,                // 最新一筆顯示在最上面
		"progressBar": true,                // 顯示隱藏時間進度條
		"positionClass": "toast-top-right", // 位置的類別
		"preventDuplicates": false,         // 隱藏重覆訊息
		"onclick": null,                    // 當點選提示訊息時，則執行此函式
		"showDuration": "300",              // 顯示時間(單位: 毫秒)
		"hideDuration": "1000",             // 隱藏時間(單位: 毫秒)
		"timeOut": "5000",                  // 當超過此設定時間時，則隱藏提示訊息(單位: 毫秒)
		"extendedTimeOut": "1000",          // 當使用者觸碰到提示訊息時，離開後超過此設定時間則隱藏提示訊息(單位: 毫秒)
		"showEasing": "swing",              // 顯示動畫時間曲線
		"hideEasing": "linear",             // 隱藏動畫時間曲線
		"showMethod": "fadeIn",             // 顯示動畫效果
		"hideMethod": "fadeOut"             // 隱藏動畫效果
	};
});

$('input[data-type=date]').bootstrapMaterialDatePicker({
	weekStart: 0,
	time: false,
	switchOnClick: true,
	lang: 'zh-tw',
	cancelText: '取消',
	okText: '確定'
});

$('input[data-type=time]').bootstrapMaterialDatePicker({
	format: 'HH:mm',
	date: false,
	switchOnClick: true,
	lang: 'zh-tw',
	cancelText: '取消',
	okText: '確定',
});

$('input[data-type=datetime]').bootstrapMaterialDatePicker({
	switchOnClick: true,
	format: 'YYYY-MM-DD HH:mm',
	lang: 'zh-tw',
	cancelText: '取消',
	okText: '確定'
});

$('.logout').click( function() {
	$.ajax({
		url: siteRootUrl + 'action/tool/logout',
		success: function (re) {
			console.log(re);
			location.reload();
		},
		error: function (a, b, c) {
			console.log("系統發生錯誤" + a.responseText);
		}
	});
});

if( $(".selectCity").length > 0 ) {
	$.ajax({
		url: siteRootUrl + 'action/tool/getCity',
		type: 'GET',
		async: false,
		success: function (re) {
			res = JSON.parse(re);
			$.each(res, function (i, item) {
				$(".selectCity").append($("<option></option>").attr("value", item).text( item ));
			});
			$(".selectCity").val($(".selectCity").data('city'));
		},
		error: function (a, b, c) {
			console.log('system error');
		}
	});
}

window.onerror = function (msg, url, line) {
	$.ajax({
		url: siteRootUrl  + 'action/tool/javascriptError',
		type: 'POST',
		data: {
			msg: msg,
			url: url,
			line: line,
		},
		success: function (re) {},
		error: function (a, b, c) {}
	});
};

function isPhone(phone) {
	if (phone.match(/^09[0-9]{8}$/)) return true;
	else return false;
}

$('.custom-control-label').click(function() {
	var checkboxItem = $(this).closest('.custom-switch').find('.custom-control-input');
	var switchStatus = (checkboxItem.prop("checked")) ? false:true;
	checkboxItem.prop("checked", switchStatus);
});

function htmlDecode(text) {
	var parser = new DOMParser;
	var dom = parser.parseFromString(
		'<!doctype html><body>' + text,
		'text/html');
	return dom.body.textContent;
}

$('.fastLogin').click(function() {
	$('#fastLogin').modal('show');
});

$('.selectidentity').click(function() {
	$('.selectidentity').removeClass('active');
	$(this).addClass('active');
	$('#loginIdentity').val($(this).data('identity'));
});

$('form#fastLoginForm').on('submit', function () {
	var formData = new FormData(this);
	$("body").loading({
		message: '登入中...請稍後...'
	});
	var loginUrl = siteRootUrl + 'action/custom/login';
	if ($('#loginIdentity').val() == 'investor') loginUrl = siteRootUrl + 'action/investor/login';
	setTimeout(function () {
		$.ajax({
			url: loginUrl,
			type: 'POST',
			dataType: 'json',
			data: formData,
			cache: true,
			contentType: false,
			processData: false,
			async: false,
			success: function (re) {
				if (re.return == 'success') {
					location.reload();
				} else {
					toastr.error(re.msg);
				}
				$('body').loading('stop');
			},
			error: function (a, b, c) {
				$('body').loading('stop');
				console.log("系統發生錯誤" + a.responseText);
			}
		});
		$('body').loading('stop');
		return false;
	}, 100);
	return false;
});