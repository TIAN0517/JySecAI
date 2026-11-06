package records

import "testing"

// TestFormatCSVColumnSelection 釘住 CSV 匯出的欄位選取規則。
//
// 為什麼要有這個測試：匯出走的是 records.FormatCSV，前端表格走的是
// web/static/js/records.js 的 renderTable。兩邊本來必須是同一套規則，
// 但 FormatCSV 只會照 def.Columns 硬列，沒有做前端那兩件事：
//
//  1. 丟掉「整個型別都沒有值」的宣告欄位 → 匯出檔會出現整欄空白
//  2. 補上「資料裡有值但型別沒宣告」的欄位 → 真正的資料會從匯出檔消失
//
// 這兩件事在 2026-11-06 實測都發生了（member_profile 11 欄中 7 欄全空，
// 且真正有內容的 channel／business 完全沒被匯出），所以在這裡釘死。
func TestFormatCSVColumnSelection(t *testing.T) {
	def := &TypeDef{
		ID: "member_profile",
		Columns: []Column{
			{Key: "member_no", Label: "會員號"},
			{Key: "name", Label: "姓名"},    // 整型別無值 → 應被丟掉
			{Key: "address", Label: "地址"}, // 只有一筆有值 → 應保留
		},
	}
	rows := []Record{
		{TypeID: "member_profile", Fields: map[string]string{
			"member_no": "M001", "name": "", "address": "台北市",
			"channel": "中租會員中心", "business": "房貸",
		}},
		{TypeID: "member_profile", Fields: map[string]string{
			"member_no": "M002", "name": "  ", "address": "",
			"channel": "中租會員中心", "business": "",
		}},
	}

	header, body := FormatCSV(def, rows)

	// 額外欄位（資料有、型別沒宣告）固定以 key 字母排序輸出，
	// 因為 Go 的 map 迭代順序不保穩定，排序才能讓匯出檔可 diff。
	wantHeader := []string{"會員號", "地址", "business", "channel"}
	if len(header) != len(wantHeader) {
		t.Fatalf("欄位數不符：got %v want %v", header, wantHeader)
	}
	for i := range wantHeader {
		if header[i] != wantHeader[i] {
			t.Fatalf("欄位[%d] 不符：got %q want %q（整組 got %v）", i, header[i], wantHeader[i], header)
		}
	}
	if len(body) != 2 {
		t.Fatalf("資料列數不符：got %d want 2", len(body))
	}
	for i, line := range body {
		if len(line) != len(wantHeader) {
			t.Fatalf("資料列[%d] 欄位數不符：got %d want %d（%v）", i, len(line), len(wantHeader), line)
		}
	}
	// 第一筆：會員號 M001、地址有值、business 有值、channel 有值
	if body[0][0] != "M001" || body[0][1] != "台北市" || body[0][2] != "房貸" || body[0][3] != "中租會員中心" {
		t.Fatalf("資料列[0] 值不符：%v", body[0])
	}
	// 第二筆：地址空、business 空，但欄位本身要存在
	if body[1][1] != "" || body[1][2] != "" {
		t.Fatalf("資料列[1] 空值處理不符：%v", body[1])
	}
}

// TestFormatCSVWithoutTypeDef 沒有型別定義時（匯出全部型別）要退回通用欄位。
func TestFormatCSVWithoutTypeDef(t *testing.T) {
	rows := []Record{
		{TypeID: "asset", Dataset: "ds", Title: "T1", ExtractedAt: "2026-11-06", Fields: map[string]string{"host": "h"}},
	}
	header, body := FormatCSV(nil, rows)
	want := []string{"類型", "資料集", "標題", "擷取時間"}
	if len(header) != len(want) {
		t.Fatalf("欄位數不符：got %v want %v", header, want)
	}
	for i := range want {
		if header[i] != want[i] {
			t.Fatalf("欄位[%d] 不符：got %q want %q", i, header[i], want[i])
		}
	}
	if len(body) != 1 || body[0][0] != "asset" || body[0][2] != "T1" {
		t.Fatalf("資料列值不符：%v", body)
	}
}

// TestFormatCSVAllColumnsEmpty 型別的宣告欄位全部無值、資料也沒有多餘欄位時，
// 不能匯出空標題列，要退回通用欄位（否則會產生只有空白的 CSV）。
func TestFormatCSVAllColumnsEmpty(t *testing.T) {
	def := &TypeDef{
		ID:      "empty_type",
		Columns: []Column{{Key: "never", Label: "從未出現"}},
	}
	rows := []Record{
		{TypeID: "empty_type", Dataset: "ds", Title: "T1", ExtractedAt: "2026-11-06", Fields: map[string]string{}},
	}
	header, body := FormatCSV(def, rows)
	if len(header) == 0 {
		t.Fatalf("欄位不可為空")
	}
	if header[0] != "類型" {
		t.Fatalf("全部欄位無值時應退回通用欄位，got %v", header)
	}
	if len(body) != 1 || len(body[0]) != len(header) {
		t.Fatalf("資料列與欄位數不符：%v vs %v", body, header)
	}
}
