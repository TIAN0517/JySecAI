app.factory('baseHttp', function ($rootScope, $http, urlSetting) {
	function errorCallback(error) {
		alert('Oops ! has error ! try it again !');
	}

	function doService(url, params, callback, error) {
		if (params == null) { params = {}; }
		$http.post(url, params).then(
			function (response) {
				callback(response.data, response.status, response.headers, response.config);
			},
			errorCallback
		);
	}
	return {
		service: function (url, params, callback, error) {
			url = urlSetting.serviceUrl + url;
			doService(url, params, callback, error);
		}
	}
})


app.factory('util', function ($rootScope, $http, $modal) {
	return {
		alert: function (msg, callback, size) {
			size = size || 'sm';
			$modal.open({
				templateUrl: 'modules/common/views/alert.html',
				backdrop: 'static',
				controller: function ($scope, $modalInstance) {
					$scope.msg = msg;
					$scope.close = function () {
						$modalInstance.dismiss('cancel');
						if (callback) callback();
					};
				}, size: size
			});
		},
		confirm: function (msg, callback) {
			$modal.open({
				templateUrl: 'modules/common/views/confirm.html',
				backdrop: 'static',
				controller: function ($scope, $modalInstance) {
					$scope.msg = msg;
					$scope.close = function (r) {
						$modalInstance.dismiss('cancel');
						if (r == true || r == false)
							if (callback) callback(r);
					};
				}, size: 'sm'
			});
		},
		isEmpty: function (obj) {
			if (obj == null) return true;
			if (obj.length > 0) return false;
			if (obj.length === 0) return true;
			if (typeof obj == "number") return false;
			if (typeof obj == "boolean") return false;
			if (typeof obj !== "object") return true;
			for (var key in obj) {
				if (hasOwnProperty.call(obj, key)) return false;
			}
			return true;
		},
		isNotEmpty: function (obj) {
			return !this.isEmpty(obj);
		},
		clone: function (obj) {
			var newObj = JSON.parse(JSON.stringify(obj));
			return newObj;
		},
		refreshDataTable: function (table, list) {
			table.clear().draw();
			table.rows.add(list);
			table.columns.adjust().draw();
		},
		getAsiaTimezone: function () {
			var _hourOffset = 8 * 60 * 60000; 	//	GMT+h*60*60000 = ms 
			var _userOffset = _date.getTimezoneOffset() * 60000;	//min*60000 = ms
			var _nowDate = new Date(_date.getTime() + _helsenkiOffset + _userOffset);
			return _nowDate;
		},
		formatDate: function (date) {
			var d = new Date(date),
				month = '' + (d.getMonth() + 1),
				day = '' + d.getDate(),
				year = d.getFullYear();

			if (month.length < 2) month = '0' + month;
			if (day.length < 2) day = '0' + day;
			return [year, month, day].join('-');
		},
		compareDate: function (startDate, endDate) {
			if (startDate <= endDate && endDate >= startDate) {
				return true;
			} else {
				return false;
			}
		},
		getNowDate: function () {
			function formatDate(date) {
				var d = new Date(date),
					month = '' + (d.getMonth() + 1),
					day = '' + d.getDate(),
					year = d.getFullYear();

				if (month.length < 2) month = '0' + month;
				if (day.length < 2) day = '0' + day;
				return [year, month, day].join('-');
			}

			var now = new Date();
			return formatDate(now.toLocaleDateString());
		},
		getTimeNow: function () {
			var now = new Date();
			h = now.getHours();
			m = now.getMinutes();
			s = now.getSeconds();
			if (m < 10) m = '0' + m;
			if (s < 10) s = '0' + s;

			return h + ':' + m + ':' + s;
		},
		fixTimerLessTen: function (t) {
			if (t < 10) {
				return '0' + t;
			} else {
				return t;
			}
		},
		checkElementCount: function (array, value, limitCount) {
			var count = 0;
			for (var i = 0; i < array.length; i++) {
				if (array[i]) {
					if (array[i] + '' == value + '') {
						count++;
						if (count >= limitCount) {
							return false;
						}
					}
				} else {
					count++;
					if (count >= limitCount) {
						return false;
					}
				}
			}
			return true;
		},
		floatFormat: function (number, n) {
			var _pow = Math.pow(10, n);
			return Math.round(number * _pow) / _pow;
		},
		encode4HTML: function (str) {
			return str
				.replace(/\r\n?/g, '\n')
				.replace(/(^((?!\n)\s)+|((?!\n)\s)+$)/gm, '')
				.replace(/(?!\n)\s+/g, ' ')
				.replace(/^\n+|\n+$/g, '')
				.replace(/[<>&"']/g, function (a) {
					switch (a) {
						case '<': return '&lt;';
						case '>': return '&gt;';
						case '&': return '&amp;';
						case '"': return '&quot;';
						case '\'': return '&apos;';
					}
				})
				.replace(/\n{2,}/g, '</p><p>')
				.replace(/\n/g, '<br />')
				.replace(/^(.+?)$/, '<p>$1</p>');
		}
	}
});

app.directive('convertToNumber', function () {
	return {
		require: 'ngModel',
		link: function (scope, element, attrs, ngModel) {
			ngModel.$parsers.push(function (val) {
				return val != null ? parseInt(val, 10) : null;
			});
			ngModel.$formatters.push(function (val) {
				return val != null ? '' + val : null;
			});
		}
	};
});

app.directive('booleanConvertToNumber', function () {
	return {
		require: 'ngModel',
		link: function (scope, element, attrs, ngModel) {
			ngModel.$parsers.push(function (val) {
				if (val != null) {
					if (val) {
						return 1;
					} else {
						return 0;
					}
				} else {
					return null;
				}
			});

			ngModel.$formatters.push(function (val) {
				if (val != null) {
					if (val === 1) {
						return true;
					} else if (val === 0) {
						return false;
					} else {
						return null;
					}
				} else {
					return null;
				}
			});
		}
	};
});


app.factory('Base64', function () {
	var keyStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
	return {
		encode: function (input) {
			var output = "";
			var chr1, chr2, chr3 = "";
			var enc1, enc2, enc3, enc4 = "";
			var i = 0;

			do {
				chr1 = input.charCodeAt(i++);
				chr2 = input.charCodeAt(i++);
				chr3 = input.charCodeAt(i++);

				enc1 = chr1 >> 2;
				enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
				enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
				enc4 = chr3 & 63;

				if (isNaN(chr2)) {
					enc3 = enc4 = 64;
				} else if (isNaN(chr3)) {
					enc4 = 64;
				}

				output = output +
					keyStr.charAt(enc1) +
					keyStr.charAt(enc2) +
					keyStr.charAt(enc3) +
					keyStr.charAt(enc4);
				chr1 = chr2 = chr3 = "";
				enc1 = enc2 = enc3 = enc4 = "";
			} while (i < input.length);

			return output;
		},
		decode: function (input) {
			var output = "";
			var chr1, chr2, chr3 = "";
			var enc1, enc2, enc3, enc4 = "";
			var i = 0;
			var base64test = /[^A-Za-z0-9\+\/\=]/g;
			if (base64test.exec(input)) { }
			input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

			do {
				enc1 = keyStr.indexOf(input.charAt(i++));
				enc2 = keyStr.indexOf(input.charAt(i++));
				enc3 = keyStr.indexOf(input.charAt(i++));
				enc4 = keyStr.indexOf(input.charAt(i++));

				chr1 = (enc1 << 2) | (enc2 >> 4);
				chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
				chr3 = ((enc3 & 3) << 6) | enc4;

				output = output + String.fromCharCode(chr1);
				if (enc3 != 64) {
					output = output + String.fromCharCode(chr2);
				}
				if (enc4 != 64) {
					output = output + String.fromCharCode(chr3);
				}

				chr1 = chr2 = chr3 = "";
				enc1 = enc2 = enc3 = enc4 = "";
			} while (i < input.length);

			return output;
		}
	}
})