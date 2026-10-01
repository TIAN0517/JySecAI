//example
app.filter('applicationStatus', function () {
	return function (number) {
		if (number === 1) {
			return "已送件";
		} else if (number === 21) {
			return "審核中";
		} else if (number === 31) {
			return "待補件";
		} else if (number === 99) {
			return "審核成功";
		} else if (number === 88) {
			return "審核失敗";
		} else {
			return "";
		}
	}
});

app.filter('courseStatus', function () {
	return function (number) {
		if (number === 0) {
			return "未滿額";
		} else if (number === 1) {
			return "已滿額";
		} else {
			return ""
		}
	}
});

app.filter('region', function () {
	return function (number) {
		if (number === 01) {
			return "基隆市";
		} else if (number === 02) {
			return "台北市";
		} else if (number === 03) {
			return "新北市";
		}  else if (number === 04) {
			return "桃園市";
		}  else if (number === 05) {
			return "新竹市";
		}  else if (number === 06) {
			return "新竹縣";
		}  else if (number === 07) {
			return "苗栗縣";
		}  else if (number === 08) {
			return "台中市";
		}  else if (number === 09) {
			return "彰化縣";
		}  else if (number === 10) {
			return "南投縣";
		}  else if (number === 11) {
			return "雲林縣";
		}  else if (number === 12) {
			return "嘉義市";
		}  else if (number === 13) {
			return "嘉義縣";
		}  else if (number === 14) {
			return "台南市";
		}  else if (number === 15) {
			return "高雄市";
		}  else if (number === 16) {
			return "屏東縣";
		}  else if (number === 17) {
			return "台東縣";
		}  else if (number === 18) {
			return "花蓮縣";
		}  else if (number === 19) {
			return "宜蘭縣";
		}  else if (number === 20) {
			return "澎湖縣";
		}  else if (number === 21) {
			return "金門縣";
		}  else if (number === 22) {
			return "連江縣";
		} else {
			return ""
		}
	}
});