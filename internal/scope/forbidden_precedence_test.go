package scope

import (
	"context"
	"testing"
)

// 禁區優先（設計 §6）：禁區永遠優先於任何授權。
//
// 測試用的目標都用 RFC 2606 保留網域（.example.test），但仍會觸發禁區規則：
// 禁區規則比對的是網域樣式（tfd.gov / epcr / 119.gov…），
// 把這些樣式放在保留網域裡既能驗證規則生效，也不會指向真實資產。

func TestForbiddenBeatsExplicitScopeCoverage(t *testing.T) {
	db := newScopeTestDB(t)
	// 明確把禁區目標寫進常駐集——這正是要驗證「擋得住」的情境。
	insertTarget(t, db, "t-forbidden", "self", "host", "tfd.gov.example.test", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"tfd.gov.example.test"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("禁區目標不該被授權：%v", coveredTargets(result))
	}
	if len(result.Uncovered) != 0 {
		t.Fatalf("禁區目標不該算未覆蓋（它是永遠不該碰，不是還沒授權）：%v", uncoveredTargets(result))
	}
	if len(result.Denied) != 1 {
		t.Fatalf("禁區目標應被拒絕一次：%v", result.Denied)
	}
	if result.Denied[0].Reason != ReasonForbidden {
		t.Fatalf("應回報 forbidden，實際 %q", result.Denied[0].Reason)
	}
	if result.Denied[0].Detail == "" {
		t.Fatal("禁區拒絕應帶上原因說明")
	}
}

func TestForbiddenBeatsGrant(t *testing.T) {
	db := newScopeTestDB(t)
	insertGrant(t, db, "g-forbidden", "host", "epcr.example.test", nil, 1, 0, nil, "active")
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"epcr.example.test"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("授權券不能覆蓋禁區：%v", coveredTargets(result))
	}
	if reason := denialFor(result, "epcr.example.test"); reason != ReasonForbidden {
		t.Fatalf("應回報 forbidden，實際 %q", reason)
	}
}

func TestForbiddenBeatsWildcardScope(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-wild-forbidden", "self", "wildcard", "*.gov.example.test", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"tfd.gov.example.test"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("wildcard 授權不能覆蓋禁區：%v", coveredTargets(result))
	}
	if reason := denialFor(result, "tfd.gov.example.test"); reason != ReasonForbidden {
		t.Fatalf("應回報 forbidden，實際 %q", reason)
	}
}

func TestForbiddenURLTargetIsDenied(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-url-forbidden", "self", "url_prefix", "https://epcr.example.test/", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"https://epcr.example.test/admin"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("禁區 URL 目標不該被授權：%v", coveredTargets(result))
	}
	if reason := denialFor(result, "https://epcr.example.test/admin"); reason != ReasonForbidden {
		t.Fatalf("應回報 forbidden，實際 %q", reason)
	}
}

func TestForbiddenStillWinsOverPermanentBlockCheck(t *testing.T) {
	db := newScopeTestDB(t)
	service := NewService(db)

	// 禁區優先於動作類別判定：禁區目標回報 forbidden（不是 permanent_block）。
	result, err := service.Resolve(context.Background(),
		[]string{"tfd.gov.example.test"}, ActionDestructive, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "tfd.gov.example.test"); reason != ReasonForbidden {
		t.Fatalf("應回報 forbidden，實際 %q", reason)
	}
}

func TestForbiddenAppliesToEveryActionClass(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-forbidden", "self", "host", "tfd.gov.example.test",
		[]string{ActionCredentialEnum, ActionBulkScan, ActionArbitrary}, nil, nil)
	service := NewService(db)

	for _, class := range []string{
		ActionLocalAnalysis, ActionHarmlessRequest, ActionCredentialEnum,
		ActionBulkScan, ActionArbitrary,
	} {
		result, err := service.Resolve(context.Background(),
			[]string{"tfd.gov.example.test"}, class, testNow)
		if err != nil {
			t.Fatal(err)
		}
		if len(result.Covered) != 0 {
			t.Fatalf("動作類別 %s 下禁區仍不得被授權", class)
		}
		if reason := denialFor(result, "tfd.gov.example.test"); reason != ReasonForbidden {
			t.Fatalf("動作類別 %s 應回報 forbidden，實際 %q", class, reason)
		}
	}
}
