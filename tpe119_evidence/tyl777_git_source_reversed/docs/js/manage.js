$('#header-dropdown').click(function (e) {
	$('#header-dropdown-menu').toggleClass('show');
});

$('#sidebar-menu li a').click(function (e) {
	$('#header-dropdown-menu').removeClass('show');
	if ($(this).attr('href') == '#' || $(this).attr('href') == '') {
		var isOpen = false;
		if ($(this).closest('li').is('.open')) isOpen = true;
		/* 關閉其他已展開的列表
		$('#sidebar-menu li').each(function () {
			$(this).removeClass('open');
			$(this).find('ul:first').removeClass('open');
		});
		*/
		if (isOpen) {
			$(this).closest('li').removeClass('open');
			$(this).closest('li').find('ul:first').removeClass('open');
		} else {
			$(this).closest('li').addClass('open');
			$(this).closest('li').find('ul:first').addClass('open');
		}
		return false;
	}
});

$('#sidebar-collapse-btn').click(function (e) {
	$('#app').toggleClass('sidebar-open');
});

$('#sidebar-overlay').click(function (e) {
	$('#app').removeClass('sidebar-open');
});

$('input[data-type=date]').bootstrapMaterialDatePicker({
	weekStart: 0,
	switchOnClick: true,
	time: false,
	lang: 'zh-tw',
	nowButton: true,
	cancelText: '取消',
	okText: '確定',
	nowText: '今天'
});

$('input[data-type=time]').bootstrapMaterialDatePicker({
	format: 'HH:mm',
	date: false,
	switchOnClick: true,
	lang: 'zh-tw',
	nowButton: true,
	cancelText: '取消',
	okText: '確定',
	nowText: '現在'
});

$('input[data-type=datetime]').bootstrapMaterialDatePicker({
	switchOnClick: true,
	format: 'YYYY-MM-DD HH:mm',
	lang: 'zh-tw',
	nowButton: true,
	cancelText: '取消',
	okText: '確定',
	nowText: '現在'
});

$('textarea[data-type=summernote]').summernote({
	callbacks: {
		onImageUpload: function (files) {
			var thisSummer = $(this);
			var formData = new FormData();
			formData.append('files', files[0]);
			$.ajax({
				url: siteRootUrl + 'manage/action/summernoteUploadImg',
				type: 'POST',
				data: formData,
				processData: false,
				contentType: false,
				dataType: 'json',
				success: function (data) {
					if (typeof data.message !== 'undefined') {
						swal({
							type: 'error',
							title: data.message,
						});
					} else {
						thisSummer.summernote('insertImage', data.url);
					}
				},
				error: function (err) {
					console.log('upload_error', err);
				}
			});
		}
	},
	toolbar: [
		['fontsize', ['fontsize']],
		['style', ['style']],
		['font', ['bold', 'italic', 'underline', 'clear']],
		['fontname', ['fontname']],
		['color', ['color']],
		['para', ['ul', 'ol', 'paragraph']],
		['height', ['height']],
		['table', ['table']],
		['insert', ['link', 'picture', 'hr']],
		['view', ['fullscreen', 'codeview']],
		['help', ['help']]
	],
	imageTitle: {
		specificAltField: true,
	},
	popover: {
		image: [
			['imagesize', ['imageSize100', 'imageSize50', 'imageSize25']],
			['float', ['floatLeft', 'floatRight', 'floatNone']],
			['remove', ['removeMedia']],
			['custom', ['imageTitle']],
		],
	},
	fontSizes: ['8', '9', '10', '11', '12', '14', '16', '18', '20', '22', '24', '26', '28', '30', '32', '34', '36', '48', '54', '60', '64', '72', '82', '150'],
	lang: 'zh-TW',
	minHeight: 450,
	maxHeight: 450,
	disableDragAndDrop: false,
	placeholder: '請輸入內容'
});

$('input[data-type=file]').on('change', function () {
	var fileText = $(this).closest('.fileUpload-btn').find('.fileUpload-text');
	if (this.files && this.files[0]) {
		fileText.html(this.files[0].name);
	} else {
		fileText.html('請點擊上傳檔案');
	}
});

$("input[data-type=imgFile]").each(function () {
	var preview = $(this).closest('.imgUpload-area').find('.imgUpload-preview');
	var clear = $(this).closest('.imgUpload-area').find('.imgUpload-clear');
	if (preview.find('img').attr('src') != '') {
		preview.css("display", "block");
		clear.css("display", "block");
		preview.find('input[type=hidden]').val('');
	}
});


$('input[data-type=imgFile]').on('change', function () {
	var preview = $(this).closest('.imgUpload-area').find('.imgUpload-preview');
	var clear = $(this).closest('.imgUpload-area').find('.imgUpload-clear');
	if (this.files && this.files[0]) {
		file = $(this).get(0).files[0];
		if (file.size < 2097152 && file.type.match("image/jpeg|image/jpg|image/png|image/gif")) {
			var reader = new FileReader();
			reader.addEventListener("load", function (event) {
				preview.find('img').attr('src', event.target.result);
				preview.css("display", "block");
				clear.css("display", "block");
				preview.find('input[type=hidden]').val('');
			});
			reader.readAsDataURL(file);
		} else if (!file.type.match("image/jpeg|image/jpg|image/png|image/gif")) {
			swal({
				type: 'error',
				title: "請上傳[PNG、JPG、JPEG、GIF]格式圖片",
			});
		} else {
			swal({
				type: 'error',
				title: "圖片檔案大小超過2M",
			});
		}
	} else {
		preview.css("display", "none");
		preview.find('input[type=hidden]').val('remove');
	}
});

$('.imgUpload-clear').click(function () {
	var preview = $(this).closest('.imgUpload-area').find('.imgUpload-preview');
	var file = $(this).closest('.imgUpload-area').find('input[data-type=imgFile]');
	file.after(file.clone(true, true).val(""));
	file.remove();
	preview.find('img').attr('src', '');
	preview.find('input[type=hidden]').val('remove');
	preview.css("display", "none");
	$(this).css("display", "none");
});

$('form#searchForm').on('click', '.search', function () {
	$('form#searchForm').submit();
});

$('form#submitForm').on('submit', function () {
	var form = $(this);
	var submitURL = form.find('input.submitURL[type=hidden]').val();
	var listURL = form.find('input.listURL[type=hidden]').val();
	var formType = form.find('input.formType[type=hidden]').val();

	formType = formType.split(",");

	if (formType.indexOf("ckPassword") >= 0) {
		var passwd = form.find('.password').val();
		var ckpasswd = form.find('.ckPassword').val();
		if (passwd != ckpasswd) {
			swal({
				type: 'error',
				title: "密碼與密碼確認不符"
			});
			return false;
		}
	}

	var formData = new FormData(this);
	if ($(this).find('input:checkbox').length > 0) {
		var checkboxList = [];
		$(this).find('input:checkbox').each(function (i) {
			var checkboxName = $(this).attr('name');
			if (!$.inArray(checkboxName, checkboxList) >= 0 ){
				checkboxList[i] = checkboxName;
				$('input:checkbox:checked[name="' + checkboxName + '"]').each(function (i) { 
					formData.set(checkboxName + '['+ i +']', this.value);
				});
			}
		});
	}
	
	$("body").loading({
		message: '資料已送出...請稍後...'
	});
	setTimeout(function () {
		$.ajax({
			url: submitURL,
			type: 'POST',
			data: formData,
			cache: true,
			contentType: false,
			processData: false,
			async: false,
			success: function (re) {
				$('body').loading('stop');
				if (re == 'success') {
					toastr["success"]("資料已儲存");
					if (listURL != '') document.location.href = listURL;
				} else {
					toastr["error"](re);
				}
			},
			error: function (a, b, c) {
				$('body').loading('stop');
				toastr["error"]("系統發生錯誤" + a.responseText);
			}
		});
		$('body').loading('stop');
		return false;
	}, 100);
	return false;
});

$(document).ready(function () {
	$('table').basictable();

	toastr.options = {
		"closeButton": false, // 顯示關閉按鈕
		"debug": false, // 除錯
		"newestOnTop": true, // 最新一筆顯示在最上面
		"progressBar": true, // 顯示隱藏時間進度條
		"positionClass": "toast-top-right", // 位置的類別
		"preventDuplicates": false, // 隱藏重覆訊息
		"onclick": null, // 當點選提示訊息時，則執行此函式
		"showDuration": "300", // 顯示時間(單位: 毫秒)
		"hideDuration": "1000", // 隱藏時間(單位: 毫秒)
		"timeOut": "5000", // 當超過此設定時間時，則隱藏提示訊息(單位: 毫秒)
		"extendedTimeOut": "1000", // 當使用者觸碰到提示訊息時，離開後超過此設定時間則隱藏提示訊息(單位: 毫秒)
		"showEasing": "swing", // 顯示動畫時間曲線
		"hideEasing": "linear", // 隱藏動畫時間曲線
		"showMethod": "fadeIn", // 顯示動畫效果
		"hideMethod": "fadeOut" // 隱藏動畫效果
	};
});

$('input[data-type=tableChekbox]').on('change', function () {
	var cb_value = $(this).closest('tr').data('id');
	var cd_status = ($(this).is(":checked")) ? '1' : '0';
	var table = $(this).data('t');
	var field = $(this).data('f');
	var idField = $(this).data('df');
	if (field == 'wish_status') return false;
	$.ajax({
		type: "POST",
		url: siteRootUrl + 'manage/action/itemCheck',
		data: {
			t: table,
			f: field,
			d: cb_value,
			v: cd_status,
			df: idField
		},
		success: function (re) {
			if (re == 'success') {
				toastr["success"]("資料已儲存");
			} else {
				toastr["error"](re);
			}
		},
		error: function (e) {}
	});
});

$('.function-btn.delete').click(function () {
	swal({
		title: '確定刪除該資料？',
		text: "刪除後，將會無法復原！",
		type: 'warning',
		dangerMode: true,
		buttons: ["取消", "確定刪除"],
	}).then((result) => {
		url = $(this).attr('href');
		if (result.value) {
			$.ajax({
				type: "GET",
				url: url,
				success: function (re) {
					if (re == 'success') {
						toastr["success"]("資料已儲存");
						location.reload();
					} else {
						toastr["error"](re);
					}
				}
			});
		}
	});
	return false;
});

$('.function-btn.doit').click(function () {
	url = $(this).attr('href');
	$.ajax({
		type: "GET",
		url: url,
		success: function (re) {
			re = JSON.parse(re);
			switch (re.status) {
				case 'success':
				case 'warning':
				case 'error':
					swal({
						type: re.status,
						title: re.message
					});
					break;
				case 'url':
					document.location.href = re.message;
					break;
				default:
					swal({
						type: 'error',
						title: "系統發生錯誤",
					});
			}
		}
	});
	return false;
});

$("select[data-type=city]").change(function () {
	var city = $(this).find(":selected").val();
	console.log(city);
	$.ajax({
		type: "POST",
		data: {
			city: city
		},
		dataType: 'json',
		url: siteRootUrl + 'manage/action/getCityArea',
		success: function (data) {
			$("select[data-type=cityArea] option").remove();
			for (var i = 0; i < data.length; i++) {
				$("select[data-type=cityArea]").append($("<option></option>").attr("value", data[i]).text(data[i]));
			}
		},
		error: function (a, b, c) {
			$("select[data-type=cityArea] option").remove();
			$("select[data-type=cityArea]").append($("<option></option>").attr("value", "").text("請先選擇縣市"));
			console.log(a.responseText);
		}
	});
});