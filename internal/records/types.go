package records

// BuiltinTypes 內建資料型別定義。
//
// 這裡的欄位不是裝飾：每一欄都對應真實靶站抽出來的欄位名，欄位定義同時決定
//   - 前端表格要排哪幾欄、用什麼標籤
//   - 去重鍵要用哪些欄位組合（見 DedupeFields）
//   - 分頁列表上方的「分類」下拉要用哪一欄（見 FacetColumn）
//
// 新增一種資料型別不需要改前端：先在這裡加一個定義，前端就會自動多出
// 一個分類頁籤與對應欄位。
func BuiltinTypes() []TypeDef {
	return []TypeDef{
		{
			// 新鑫房貸批次匯出（多工作表：五千七百二十七／三千條／一千條／一百條）。
			// 欄位以原表標題為準：房貸公司、日期、姓名、身分證、性別、手機、市話、
			// 公司名稱、公司統編、公司電話、房屋住址、房貸金額、期數、利率、月付款、
			// 保證人…、核貸金額、核貸期數、核貸利率、核貸月付款、聯絡人、聯絡人電話。
			ID:           "loan_case",
			Label:        "房貸申請",
			Description:  "房貸公司 × 申請人／保證人資料（本案房貸公司為新鑫）。欄位含 電話／地址／貸款金額／期數／貸款日期／車牌；此來源沒有地址與車牌的值，欄位保留是為了跟其他貸款來源對齊。公司名稱欄是借貸人的雇主，不是資料來源。",
			Icon:         "🏦",
			FacetColumn:  "loan_company",
			DedupeFields: []string{"id_number", "apply_date", "loan_amount", "periods"},
			Columns: []Column{
				{Key: "loan_company", Label: "房貸公司", Kind: "text", Norm: "text", Facet: true},
				{Key: "apply_date", Label: "貸款日期", Kind: "date", Norm: "text"},
				{Key: "name", Label: "姓名", Kind: "text", Norm: "text"},
				{Key: "id_number", Label: "身分證", Kind: "text", Norm: "alnum"},
				{Key: "gender", Label: "性別", Kind: "text", Norm: "text", Facet: true},
				{Key: "mobile", Label: "電話(手機)", Kind: "text", Norm: "phone", Facet: true},
				{Key: "landline", Label: "電話(市話)", Kind: "text", Norm: "digits"},
				{Key: "company_name", Label: "公司名稱(雇主)", Kind: "text", Norm: "text", Facet: true},
				{Key: "company_tax_id", Label: "公司統編", Kind: "text", Norm: "alnum"},
				{Key: "company_phone", Label: "公司電話", Kind: "text", Norm: "digits"},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "loan_amount", Label: "貸款金額", Kind: "money", Norm: "digits"},
				{Key: "periods", Label: "期數", Kind: "int", Norm: "digits", Facet: true},
				{Key: "interest_rate", Label: "利率", Kind: "text", Norm: "text"},
				{Key: "monthly_payment", Label: "月付款", Kind: "money", Norm: "digits"},
				{Key: "guarantor", Label: "保證人", Kind: "text", Norm: "text"},
				{Key: "guarantor_id", Label: "保證人身分證", Kind: "text", Norm: "alnum"},
				{Key: "guarantor_phone", Label: "保證人電話", Kind: "text", Norm: "digits"},
				{Key: "guarantor_gender", Label: "保證人性別", Kind: "text", Norm: "text"},
				{Key: "guarantor2", Label: "保證人2", Kind: "text", Norm: "text"},
				{Key: "guarantor2_id", Label: "保證人2身分證", Kind: "text", Norm: "alnum"},
				{Key: "guarantor2_phone", Label: "保證人2電話", Kind: "text", Norm: "digits"},
				{Key: "guarantor2_gender", Label: "保證人2性別", Kind: "text", Norm: "text"},
				{Key: "guarantor3", Label: "保證人3", Kind: "text", Norm: "text"},
				{Key: "guarantor3_id", Label: "保證人3身分證", Kind: "text", Norm: "alnum"},
				{Key: "guarantor3_phone", Label: "保證人3電話", Kind: "text", Norm: "digits"},
				{Key: "guarantor3_gender", Label: "保證人3性別", Kind: "text", Norm: "text"},
				{Key: "approved_amount", Label: "核貸金額", Kind: "money", Norm: "digits"},
				{Key: "approved_periods", Label: "核貸期數", Kind: "int", Norm: "digits"},
				{Key: "approved_rate", Label: "核貸利率", Kind: "text", Norm: "text"},
				{Key: "approved_monthly", Label: "核貸月付款", Kind: "money", Norm: "digits"},
				{Key: "contact_name", Label: "聯絡人", Kind: "text", Norm: "text"},
				{Key: "contact_phone", Label: "聯絡人電話", Kind: "text", Norm: "digits"},
				{Key: "plate", Label: "車牌", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "source_sheet", Label: "來源工作表", Kind: "text", Norm: "text", Facet: true},
				{Key: "source_file", Label: "來源檔", Kind: "text", Norm: "text", Facet: true},
			},
		},
		{
			// 中租會員中心匿名查詢（GET /Member/UserSiteList?phone=）取得：
			// 序號、手機號(電話)、同手機號下會員號池、站台ID、渠道名稱、會員登入識別碼、
			// 簽約姓名、身份證字號、車牌號、簽約完成、簽約完成時間、建檔時間(貸款/申請日期)、已開通業務。
			ID:           "member_signup",
			Label:        "會員簽約",
			Description:  "中租會員中心（mid-sign-dev.chailease.com.tw）匿名查詢可得的會員／簽約資料，含車牌號。與新鑫房貸是不同來源。",
			Icon:         "🪪",
			FacetColumn:  "channel",
			DedupeFields: []string{"phone", "id_number", "sign_time"},
			Columns: []Column{
				{Key: "phone", Label: "電話", Kind: "text", Norm: "phone", Facet: true},
				{Key: "member_no", Label: "會員號", Kind: "text", Norm: "alnum"},
				{Key: "site_id", Label: "站台ID", Kind: "text", Norm: "text", Facet: true},
				{Key: "channel", Label: "渠道名稱", Kind: "text", Norm: "text", Facet: true},
				{Key: "login_identifier", Label: "會員登入識別碼", Kind: "text", Norm: "text"},
				{Key: "sign_name", Label: "簽約姓名", Kind: "text", Norm: "text"},
				{Key: "id_number", Label: "身份證字號", Kind: "text", Norm: "alnum"},
				{Key: "plate", Label: "車牌", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "sign_done", Label: "簽約完成", Kind: "text", Norm: "text", Facet: true},
				{Key: "sign_time", Label: "簽約完成時間", Kind: "date", Norm: "text"},
				{Key: "created_at", Label: "貸款/申請日期", Kind: "date", Norm: "text"},
				{Key: "loan_amount", Label: "貸款金額", Kind: "money", Norm: "digits"},
				{Key: "periods", Label: "期數", Kind: "int", Norm: "digits"},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "business", Label: "已開通業務", Kind: "text", Norm: "text"},
				{Key: "source_file", Label: "來源檔", Kind: "text", Norm: "text"},
			},
		},
		{
			// 和泰／Hotai 真實據點（公開 location.ashx + htcp 交叉複核）：
			// KEY、据点名称、经销商、类型、县市、区域、地址、电话、经度、纬度、营业时间、
			// AED、专属、EBIS、NTIS、BPIS、假日时间、限高类型、限高。
			ID:           "branch",
			Label:        "營業據點",
			Description:  "和泰 Hotai 據點清單（TOYOTA／LEXUS 兩套來源 schema），含據點名稱、經銷商、縣市、地址、電話、營業時間。",
			Icon:         "🏪",
			FacetColumn:  "city",
			DedupeFields: []string{"source_brand", "branch_name"},
			Columns: []Column{
				{Key: "branch_key", Label: "據點代號", Kind: "text", Norm: "alnum"},
				{Key: "branch_name", Label: "據點名稱", Kind: "text", Norm: "text"},
				{Key: "dealer", Label: "經銷商", Kind: "text", Norm: "text", Facet: true},
				{Key: "branch_type", Label: "類型", Kind: "text", Norm: "text", Facet: true},
				{Key: "city", Label: "縣市", Kind: "text", Norm: "text", Facet: true},
				{Key: "district", Label: "區域", Kind: "text", Norm: "text", Facet: true},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "phone", Label: "電話", Kind: "text", Norm: "digits"},
				{Key: "lng", Label: "經度", Kind: "text", Norm: "text"},
				{Key: "lat", Label: "緯度", Kind: "text", Norm: "text"},
				{Key: "open_hours", Label: "營業時間", Kind: "text", Norm: "text"},
				{Key: "weekday_hours", Label: "平日營業", Kind: "text", Norm: "text"},
				{Key: "postcode", Label: "郵遞區號", Kind: "text", Norm: "digits"},
				{Key: "brand_code", Label: "品牌碼", Kind: "text", Norm: "alnum"},
				{Key: "dealer_code", Label: "經銷商代碼", Kind: "text", Norm: "alnum"},
				{Key: "branch_code", Label: "據點代碼", Kind: "text", Norm: "alnum"},
				{Key: "comp_id", Label: "公司代碼", Kind: "text", Norm: "alnum"},
				{Key: "branch_id", Label: "門市代碼", Kind: "text", Norm: "alnum"},
				{Key: "wheelchair", Label: "無障礙", Kind: "text", Norm: "text"},
				{Key: "od_open", Label: "OD開", Kind: "text", Norm: "text"},
				{Key: "aed", Label: "AED", Kind: "text", Norm: "text"},
				{Key: "exclusive", Label: "專屬", Kind: "text", Norm: "text", Facet: true},
				{Key: "ebis", Label: "EBIS", Kind: "text", Norm: "text"},
				{Key: "ntis", Label: "NTIS", Kind: "text", Norm: "text"},
				{Key: "bpis", Label: "BPIS", Kind: "text", Norm: "text"},
				{Key: "holiday_hours", Label: "假日時間", Kind: "text", Norm: "text"},
				{Key: "height_limit_type", Label: "限高類型", Kind: "text", Norm: "text"},
				{Key: "height_limit", Label: "限高", Kind: "int", Norm: "digits"},
				{Key: "source_brand", Label: "來源品牌", Kind: "text", Norm: "text", Facet: true},
				{Key: "source_file", Label: "來源檔", Kind: "text", Norm: "text", Facet: true},
			},
		},
		{
			ID:           "express_order",
			Label:        "快遞訂單",
			Description:  "物流／快遞系統訂單主檔",
			Icon:         "📦",
			FacetColumn:  "status",
			DedupeFields: []string{"order_no"},
			Columns: []Column{
				{Key: "order_no", Label: "訂單編號", Kind: "text", Norm: "alnum", Facet: true, Width: 170},
				{Key: "carrier", Label: "物流商", Kind: "text", Norm: "text", Facet: true},
				{Key: "created_at", Label: "下單時間", Kind: "date", Norm: "text"},
				{Key: "receiver", Label: "收件人", Kind: "text", Norm: "text"},
				{Key: "phone", Label: "收件電話", Kind: "text", Norm: "phone"},
				{Key: "address", Label: "收件地址", Kind: "text", Norm: "text"},
				{Key: "item", Label: "貨品", Kind: "text", Norm: "text"},
				{Key: "quantity", Label: "數量", Kind: "int", Norm: "digits"},
				{Key: "amount", Label: "金額", Kind: "money", Norm: "digits"},
				{Key: "cod_amount", Label: "貨到付款", Kind: "money", Norm: "digits"},
				{Key: "status", Label: "物流狀態", Kind: "text", Norm: "text", Facet: true},
				{Key: "tracking_no", Label: "物流單號", Kind: "text", Norm: "alnum"},
				{Key: "source_table", Label: "來源表", Kind: "text", Norm: "text"},
			},
		},
		{
			// 中租 mid-sign 靶站案件主檔（既有 loan_cases.db，28,678 案）。
			// 之前只走 /api/loan/* 唯讀橋接與獨立頁面，這裡把它也收進統一主控台，
			// 讓所有資料源共用同一套「分類 → 欄位 → 分頁 → 去重」。
			ID:           "loan_case_master",
			Label:        "中租案件主檔",
			Description:  "中租 mid-sign 靶站案件主檔（案件編號、申請日區間、金額來源標記、來源表）",
			Icon:         "🗂️",
			FacetColumn:  "code_year",
			DedupeFields: []string{"case_no"},
			Columns: []Column{
				{Key: "case_no", Label: "案件編號", Kind: "text", Norm: "alnum", Facet: true, Width: 160},
				{Key: "app_count", Label: "申請單數", Kind: "int", Norm: "digits"},
				{Key: "first_apply_at", Label: "申請日最早", Kind: "date", Norm: "text"},
				{Key: "last_apply_at", Label: "申請日最晚", Kind: "date", Norm: "text"},
				{Key: "code_year", Label: "編碼年", Kind: "int", Norm: "digits", Facet: true},
				{Key: "amount_source_flag", Label: "金額來源標記", Kind: "text", Norm: "text"},
				{Key: "amount_source_detail", Label: "金額來源明細", Kind: "text", Norm: "text"},
				{Key: "source_tables", Label: "來源表", Kind: "text", Norm: "text", Facet: true},
				{Key: "orphan_case", Label: "孤兒案件", Kind: "text", Norm: "text"},
				{Key: "master_app", Label: "主表申請單", Kind: "text", Norm: "alnum"},
			},
		},
		{
			// 中租 mid-sign 申請單（31,730 筆）：欄位最豐富的一層。
			ID:           "loan_application",
			Label:        "中租申請單",
			Description:  "中租 mid-sign 靶站申請單（狀態、類型、客群、金額、期數、首末應繳日）",
			Icon:         "🧾",
			FacetColumn:  "case_status",
			DedupeFields: []string{"app_no", "case_no"},
			Columns: []Column{
				{Key: "app_no", Label: "申請單號", Kind: "text", Norm: "alnum", Facet: true, Width: 140},
				{Key: "case_no", Label: "案件編號", Kind: "text", Norm: "alnum", Facet: true, Width: 150},
				{Key: "apply_at", Label: "申請時間", Kind: "date", Norm: "text"},
				{Key: "apply_year", Label: "申請年", Kind: "int", Norm: "digits", Facet: true},
				{Key: "case_status", Label: "案件狀態", Kind: "text", Norm: "text", Facet: true},
				{Key: "case_type", Label: "案件類型", Kind: "text", Norm: "text", Facet: true},
				{Key: "customer_group", Label: "客群", Kind: "text", Norm: "text", Facet: true},
				{Key: "apply_amount", Label: "申請金額", Kind: "money", Norm: "digits"},
				{Key: "collateral_amount", Label: "擔保金額", Kind: "money", Norm: "digits"},
				{Key: "interest", Label: "利息", Kind: "money", Norm: "digits"},
				{Key: "approved_amount", Label: "核准金額", Kind: "money", Norm: "digits"},
				{Key: "total_approved", Label: "合併核准金額", Kind: "money", Norm: "digits"},
				{Key: "periods", Label: "期數", Kind: "int", Norm: "digits"},
				{Key: "total_amount", Label: "總金額", Kind: "money", Norm: "digits"},
				{Key: "first_due", Label: "首期應繳", Kind: "date", Norm: "text"},
				{Key: "last_due", Label: "末期應繳", Kind: "date", Norm: "text"},
				{Key: "amount_source", Label: "金額來源", Kind: "text", Norm: "text"},
				{Key: "source_sheet", Label: "來源表", Kind: "text", Norm: "text", Facet: true},
			},
		},

		{
			// 以「會員號」為單位的會員檔。與 member_signup（簽約記錄）的關聯是
			// 「手機號 → 會員號池」，不是一對一 —— 來源報告已載明兩端無共同鍵，
			// 所以地址／金額／期數掛在會員號上，不會掛到別人的車牌上。
			ID:           "member_profile",
			Label:        "會員檔",
			Description:  "以會員號為單位的會員資料。兩個寫入來源：生產會員全量（會員號／電話／渠道／站台／已開通業務）與會員中心補齊（地址／貸款金額／期數／利率／月付）。與簽約記錄僅以手機號→會員號池關聯，無一對一對應",
			Icon:         "👤",
			FacetColumn:  "phone",
			DedupeFields: []string{"member_no"},
			Columns: []Column{
				{Key: "member_no", Label: "會員號", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "phone", Label: "電話", Kind: "text", Norm: "phone", Facet: true},
				{Key: "site_id", Label: "站台ID", Kind: "text", Norm: "text", Facet: true},
				{Key: "channel", Label: "渠道名稱", Kind: "text", Norm: "text", Facet: true},
				{Key: "business", Label: "已開通業務", Kind: "text", Norm: "text"},
				{Key: "business_count", Label: "業務筆數", Kind: "int", Norm: "digits"},
				{Key: "login_identifier", Label: "會員登入識別碼", Kind: "text", Norm: "text"},
				{Key: "name", Label: "姓名", Kind: "text", Norm: "text"},
				{Key: "id_number", Label: "身份證字號", Kind: "text", Norm: "alnum"},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "loan_amount", Label: "貸款金額", Kind: "money", Norm: "digits"},
				{Key: "periods", Label: "期數", Kind: "int", Norm: "digits"},
				{Key: "interest_rate", Label: "利率", Kind: "text", Norm: "text"},
				{Key: "monthly_payment", Label: "月付", Kind: "money", Norm: "digits"},
				{Key: "sign_pool", Label: "同手機號下會員號池", Kind: "text", Norm: "text"},
				{Key: "source_file", Label: "來源檔", Kind: "text", Norm: "text", Facet: true},
			},
		},
		{
			// 中租 mid-sign Oracle（fleet19c）定向抽取結果：客戶主檔 UCAR_CUST_DATA
			// × 授信主檔 UCAR_APR_FORM，以「身分證／統編」為鍵。
			//
			// 為什麼是獨立型別而不是回填 member_profile：
			// Oracle 端是以身分證/統編（CUST_ID_NO ↔ APR_CUST_NO）為鍵，
			// 與「會員號」不是同一個識別碼，兩端無可驗證的一對一對應，
			// 掛回去等於製造假資料，所以另立型別；簽約記錄（member_signup）
			// 因本身就帶身分證，才由 sqli_pull_scope.py 以同一識別碼回填。
			//
			// 範圍：僅本次授權範圍內的鍵（會員簽約身分證 + 生產會員號全量手機號），
			// 不含全表 dump，避免觸及同庫其他法人主體的第三方個人資料。
			ID:           "chailease_customer",
			Label:        "中租客戶授信",
			Description:  "中租 mid-sign Oracle（fleet19c）客戶主檔×授信主檔：以身分證／統編為鍵，含地址、核貸金額、期數、利率（定向抽取，非全表）",
			Icon:         "🏦",
			FacetColumn:  "company",
			DedupeFields: []string{"cust_id_no", "case_no"},
			Columns: []Column{
				{Key: "cust_id_no", Label: "身分證／統編", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "cust_name", Label: "姓名", Kind: "text", Norm: "text"},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "county", Label: "縣市", Kind: "text", Norm: "text", Facet: true},
				{Key: "district", Label: "鄉鎮市區", Kind: "text", Norm: "text"},
				{Key: "phone", Label: "手機", Kind: "text", Norm: "phone", Facet: true},
				{Key: "salary", Label: "月薪", Kind: "money", Norm: "digits"},
				{Key: "company", Label: "服務機構", Kind: "text", Norm: "text", Facet: true},
				{Key: "case_no", Label: "案件編號", Kind: "text", Norm: "alnum"},
				{Key: "approved_amount", Label: "核貸金額", Kind: "money", Norm: "digits"},
				{Key: "periods", Label: "期數", Kind: "int", Norm: "digits"},
				{Key: "rate", Label: "利率", Kind: "text", Norm: "text"},
				{Key: "fee", Label: "手續費", Kind: "money", Norm: "digits"},
				{Key: "apply_date", Label: "申請日期", Kind: "date", Norm: "text"},
			},
		},
		{
			ID:           "credential",
			Label:        "帳號憑證",
			Description:  "從靶站驗證出的帳號／密碼組",
			Icon:         "🔑",
			FacetColumn:  "kind",
			DedupeFields: []string{"domain", "username"},
			Columns: []Column{
				{Key: "domain", Label: "網域", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "username", Label: "帳號", Kind: "text", Norm: "text"},
				{Key: "password", Label: "密碼", Kind: "text", Norm: "text"},
				{Key: "kind", Label: "類型", Kind: "text", Norm: "text", Facet: true},
				{Key: "host", Label: "來源主機", Kind: "text", Norm: "alnum"},
				{Key: "obtained_at", Label: "取得時間", Kind: "date", Norm: "text"},
				{Key: "valid", Label: "有效性", Kind: "text", Norm: "text", Facet: true},
			},
		},
		{
			ID:           "asset",
			Label:        "資產指紋",
			Description:  "掃描器辨識出的主機／服務",
			Icon:         "🛰️",
			FacetColumn:  "service",
			DedupeFields: []string{"host", "port"},
			Columns: []Column{
				{Key: "host", Label: "主機", Kind: "text", Norm: "alnum", Facet: true, Width: 150},
				{Key: "port", Label: "埠", Kind: "int", Norm: "digits"},
				{Key: "protocol", Label: "協定", Kind: "text", Norm: "text"},
				{Key: "service", Label: "服務", Kind: "text", Norm: "text", Facet: true},
				{Key: "product", Label: "產品", Kind: "text", Norm: "text"},
				{Key: "version", Label: "版本", Kind: "text", Norm: "text"},
				{Key: "title", Label: "頁面標題", Kind: "text", Norm: "text"},
				{Key: "source", Label: "來源", Kind: "text", Norm: "text", Facet: true},
				{Key: "confidence", Label: "可信度", Kind: "text", Norm: "text"},
			},
		},
		{
			ID:           "vulnerability",
			Label:        "風險漏洞",
			Description:  "已入庫、可驗證的漏洞",
			Icon:         "⚠️",
			FacetColumn:  "severity",
			DedupeFields: []string{"title", "target"},
			Columns: []Column{
				{Key: "title", Label: "標題", Kind: "text", Norm: "text", Facet: true},
				{Key: "severity", Label: "等級", Kind: "text", Norm: "text", Facet: true},
				{Key: "cvss", Label: "CVSS", Kind: "text", Norm: "text"},
				{Key: "cve", Label: "CVE", Kind: "text", Norm: "alnum"},
				{Key: "target", Label: "目標", Kind: "text", Norm: "alnum"},
				{Key: "status", Label: "狀態", Kind: "text", Norm: "text", Facet: true},
				{Key: "discovered_at", Label: "發現時間", Kind: "date", Norm: "text"},
			},
		},
		{
			ID:           "contact",
			Label:        "聯絡資料",
			Description:  "靶站流出的姓名／電話／地址",
			Icon:         "📇",
			FacetColumn:  "source",
			DedupeFields: []string{"phone"},
			Columns: []Column{
				{Key: "name", Label: "姓名", Kind: "text", Norm: "text"},
				{Key: "phone", Label: "電話", Kind: "text", Norm: "phone", Facet: true},
				{Key: "email", Label: "電子郵件", Kind: "text", Norm: "alnum"},
				{Key: "address", Label: "地址", Kind: "text", Norm: "text"},
				{Key: "source", Label: "來源", Kind: "text", Norm: "text", Facet: true},
				{Key: "obtained_at", Label: "取得時間", Kind: "date", Norm: "text"},
			},
		},
		{
			// generic 有兩個寫入來源，欄位定義取兩者的聯集：
			//   - chailease_endpoints：中租 mid-sign 靶站的 API 清單
			//     （主機／路徑／請求方式／環境狀態／類別／記錄數／協定／來源系統）
			//   - scan_runner：掃描器產出的端點（多一個 bytes 回應位元組）
			//
			// 原先宣告的 title／value／obtained_at 沒有任何寫入程式會產生：
			// 2026-11-06 實查資料庫，三者在 594 筆 generic 記錄中都是 0 筆 → 已移除。
			// （就算之後真的有資料寫進來，前端與 CSV 匯出都會自動補上未宣告欄位。）
			ID:           "generic",
			Label:        "未分類記錄",
			Description:  "未分類的提取結果：中租 mid-sign API 清單與掃描器端點（欄位依內容自動偵測）",
			Icon:         "📦",
			FacetColumn:  "source",
			DedupeFields: nil,
			Columns: []Column{
				{Key: "host", Label: "主機", Kind: "text", Norm: "alnum", Facet: true},
				{Key: "path", Label: "API 路徑", Kind: "text", Norm: "text"},
				{Key: "method", Label: "請求方式", Kind: "text", Norm: "text", Facet: true},
				{Key: "status", Label: "環境狀態", Kind: "text", Norm: "text", Facet: true},
				{Key: "category", Label: "類別", Kind: "text", Norm: "text", Facet: true},
				{Key: "note", Label: "備註", Kind: "text", Norm: "text"},
				{Key: "scheme", Label: "協定", Kind: "text", Norm: "text"},
				{Key: "origin", Label: "來源系統", Kind: "text", Norm: "text"},
				{Key: "bytes", Label: "回應位元組", Kind: "int", Norm: "digits"},
				{Key: "source", Label: "來源", Kind: "text", Norm: "text", Facet: true},
			},
		},
	}
}
