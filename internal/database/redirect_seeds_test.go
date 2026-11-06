package database

import (
	"path/filepath"
	"testing"
	"time"

	"go.uber.org/zap"
)

// 這些測試釘死「複查站點的站點清單要能自動從資料庫提取」這條鏈的核心：
// CollectRedirectVerifySeeds。
//
// 這條路徑是「掃哪一批站點」不靠人工複製網址的來源 —— 漏洞庫與資產庫裡
// 本來就有分類（娛樂城、SEO、現金版…），每筆都帶著目標主機與既有證據。
// 它有兩個關鍵行為必須被守住：
//
//  1. 關鍵字要能跨欄位比對（漏洞紀錄的 target 欄位不是乾淨網址，
//     「example.com (1.2.3.4)」這種寫法也要抽得出主機）。
//  2. 私有／回環位址必須被擋掉 —— 那通常是受害者自己系統的內網架構，
//     不是可以對外巡站的站點。

func seedTestDB(t *testing.T) *DB {
	t.Helper()
	db, err := NewDB(filepath.Join(t.TempDir(), "redirect-seeds.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func insertSeedVuln(t *testing.T, db *DB, id, title, description, target, evidence string) {
	t.Helper()
	now := time.Now().Format(time.RFC3339)
	_, err := db.Exec(`INSERT INTO vulnerabilities
		(id, title, description, severity, status, target, evidence, created_at, updated_at)
		VALUES (?, ?, ?, 'medium', 'confirmed', ?, ?, ?, ?)`,
		id, title, description, target, evidence, now, now)
	if err != nil {
		t.Fatalf("insert vulnerability %s: %v", id, err)
	}
}

func hasHost(list []string, want string) bool {
	for _, v := range list {
		if v == want {
			return true
		}
	}
	return false
}

// 資產庫來源：關鍵字要能命中 title／business_system／source_query／environment，
// 而且吐出來的一定是 https:// + 主機。
func TestCollectRedirectVerifySeedsFromAssetsMatchesClassificationFields(t *testing.T) {
	db := seedTestDB(t)

	assets := []*Asset{
		{Host: "alpha.example.com", Title: "娛樂城入口", Source: "manual"},
		{Host: "beta.example.com", Title: "官網", BusinessSystem: "SEO 投毒站群", Source: "manual"},
		{Host: "gamma.example.com", Title: "官網", SourceQuery: "現金版 關鍵字", Source: "manual"},
		// environment 有白名單（production/staging/testing/development/other），
		// 所以這個欄位能提供的分類詞彙是有限的那幾個。
		{Host: "delta.example.com", Title: "官網", Environment: "staging", Source: "manual"},
		{Host: "epsilon.example.com", Title: "無關分類", Source: "manual"},
	}
	if _, err := db.UpsertAssets(assets, ""); err != nil {
		t.Fatalf("upsert assets: %v", err)
	}

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "娛樂城", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://alpha.example.com" {
		t.Fatalf("title 比對失敗：%v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "SEO", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://beta.example.com" {
		t.Fatalf("business_system 比對失敗：%v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "現金版", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://gamma.example.com" {
		t.Fatalf("source_query 比對失敗：%v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "staging", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://delta.example.com" {
		t.Fatalf("environment 比對失敗：%v", seeds)
	}

	// 沒有命中的關鍵字 → 空清單（不是「退化成全表」）
	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "不存在分類", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 0 {
		t.Fatalf("不該有任何種子，實際 %v", seeds)
	}
}

// 漏洞紀錄來源：target 欄位常是髒的（「example.com (1.2.3.4)」），
// 而且站點常常只出現在標題或描述裡 —— 四個欄位都要能抽出主機。
func TestCollectRedirectVerifySeedsFromVulnerabilitiesExtractsMessyTargets(t *testing.T) {
	db := seedTestDB(t)

	insertSeedVuln(t, db, "v1", "娛樂城 A 站 SQLi", "注入點位於 /news.php",
		"https://vuln-alpha.example.com (203.0.113.10)", "User-Agent: curl")
	insertSeedVuln(t, db, "v2", "無關標題", "SEO 投毒群，目標 www.vuln-beta.example.com",
		"203.0.113.20:443/UDP", "CN=*.vuln-gamma.example.com")
	insertSeedVuln(t, db, "v3", "SEO 站 3", "無關描述", "203.0.113.30", "Redirected to https://vuln-delta.example.com/x")

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceVulns, "娛樂城", 10)
	if err != nil {
		t.Fatalf("collect vuln seeds: %v", err)
	}
	if !hasHost(seeds, "https://vuln-alpha.example.com") {
		t.Fatalf("應從 target 的髒網址抽出主機，實際 %v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceVulns, "SEO", 10)
	if err != nil {
		t.Fatalf("collect vuln seeds: %v", err)
	}
	if !hasHost(seeds, "https://www.vuln-beta.example.com") {
		t.Fatalf("應從描述抽出主機，實際 %v", seeds)
	}
	if !hasHost(seeds, "https://vuln-gamma.example.com") {
		t.Fatalf("應從證據抽出主機，實際 %v", seeds)
	}
	if !hasHost(seeds, "https://vuln-delta.example.com") {
		t.Fatalf("應從證據的 URL 抽出主機，實際 %v", seeds)
	}
}

// 私有／回環位址必須被擋掉：那不是可以對外巡站的站點。
func TestCollectRedirectVerifySeedsSkipsPrivateAndLoopbackHosts(t *testing.T) {
	db := seedTestDB(t)

	if _, err := db.UpsertAssets([]*Asset{
		{Host: "127.0.0.1", Title: "娛樂城 本機", Source: "manual"},
		{Host: "192.168.1.10", Title: "娛樂城 內網", Source: "manual"},
		{Host: "10.0.0.5", Title: "娛樂城 內網2", Source: "manual"},
		{Host: "localhost", Title: "娛樂城 localhost", Source: "manual"},
		{Host: "public.example.com", Title: "娛樂城 對外", Source: "manual"},
	}, ""); err != nil {
		t.Fatalf("upsert assets: %v", err)
	}

	insertSeedVuln(t, db, "v1", "娛樂城 紀錄", "描述", "192.168.2.20", "evidence")
	insertSeedVuln(t, db, "v2", "娛樂城 紀錄 2", "描述", "https://ok.example.com", "evidence")

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceAssets, "娛樂城", 10)
	if err != nil {
		t.Fatalf("collect assets seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://public.example.com" {
		t.Fatalf("私有／回環位址沒被擋掉：%v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceVulns, "娛樂城", 10)
	if err != nil {
		t.Fatalf("collect vuln seeds: %v", err)
	}
	for _, s := range seeds {
		if s == "https://192.168.2.20" {
			t.Fatalf("回環／私有位址沒被擋掉：%v", seeds)
		}
	}
	if !hasHost(seeds, "https://ok.example.com") {
		t.Fatalf("正常站點不該被一起擋掉：%v", seeds)
	}
}

// limit 要真的生效（單批種子站點數上限，避免寬鬆關鍵字就對幾百個站點發請求）。
func TestCollectRedirectVerifySeedsRespectsLimit(t *testing.T) {
	db := seedTestDB(t)

	insertSeedVuln(t, db, "v1", "娛樂城 1", "d", "https://a1.example.com", "e")
	insertSeedVuln(t, db, "v2", "娛樂城 2", "d", "https://a2.example.com", "e")
	insertSeedVuln(t, db, "v3", "娛樂城 3", "d", "https://a3.example.com", "e")
	insertSeedVuln(t, db, "v4", "娛樂城 4", "d", "https://a4.example.com", "e")

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceVulns, "娛樂城", 2)
	if err != nil {
		t.Fatalf("collect vuln seeds: %v", err)
	}
	if len(seeds) != 2 {
		t.Fatalf("limit=2 應該只回 2 個種子，實際 %d：%v", len(seeds), seeds)
	}
}

// manual 來源不從資料庫撈（目標由請求自己帶），不支援的來源要回錯。
func TestCollectRedirectVerifySeedsSourceHandling(t *testing.T) {
	db := seedTestDB(t)
	insertSeedVuln(t, db, "v1", "娛樂城 1", "d", "https://a1.example.com", "e")

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceManual, "娛樂城", 10)
	if err != nil {
		t.Fatalf("manual 不該回錯：%v", err)
	}
	if len(seeds) != 0 {
		t.Fatalf("manual 來源不該撈資料庫，實際 %v", seeds)
	}

	seeds, err = db.CollectRedirectVerifySeeds("", "娛樂城", 10)
	if err != nil {
		t.Fatalf("空來源等同 manual：%v", err)
	}
	if len(seeds) != 0 {
		t.Fatalf("空來源不該撈資料庫，實際 %v", seeds)
	}

	if _, err := db.CollectRedirectVerifySeeds("不存在的來源", "娛樂城", 10); err == nil {
		t.Fatal("不支援的來源應該回錯")
	}
}

// 空關鍵字要退化成「取最近更新的紀錄」，而不是掃全表。
func TestCollectRedirectVerifySeedsWithoutKeywordTakesRecentRecords(t *testing.T) {
	db := seedTestDB(t)

	insertSeedVuln(t, db, "old", "舊紀錄", "d", "https://old.example.com", "e")
	time.Sleep(1100 * time.Millisecond)
	insertSeedVuln(t, db, "new", "新紀錄", "d", "https://new.example.com", "e")

	seeds, err := db.CollectRedirectVerifySeeds(RedirectVerifySeedSourceVulns, "", 1)
	if err != nil {
		t.Fatalf("collect vuln seeds: %v", err)
	}
	if len(seeds) != 1 || seeds[0] != "https://new.example.com" {
		t.Fatalf("空關鍵字應取最近更新的紀錄，實際 %v", seeds)
	}
}
