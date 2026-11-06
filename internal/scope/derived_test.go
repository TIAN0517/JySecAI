package scope

import (
	"context"
	"testing"
	"time"
)

// TestDerivedTargetsSubdomainOfAuthorizedHost：授權主機的子網域可推導。
func TestDerivedTargetsSubdomainOfAuthorizedHost(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "scope_parent", "example-client", "host", "api.example.com", []string{ActionHarmlessRequest}, nil, nil)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("new.api.example.com"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 1 {
		t.Fatalf("應推導出 1 筆，得到 %d", len(derived))
	}
	if derived[0].SourceID != "scope_parent" {
		t.Fatalf("來源應為 scope_parent，得到 %q", derived[0].SourceID)
	}
	if derived[0].SourceOwner != "example-client" {
		t.Fatalf("owner 應沿用來源，得到 %q", derived[0].SourceOwner)
	}
	if len(derived[0].ActionClasses) == 0 {
		t.Fatal("動作類別應沿用來源")
	}
}

// TestDerivedTargetsSiblingIsNotDerived：只共享兩段標籤的兄弟網域不可推導。
//
// 這條是最容易被放寬過頭的地方：notapi.example.com 與 api.example.com 共享
// example.com，但它不是 api.example.com 的子網域 —— 沒有書面依據涵蓋它。
func TestDerivedTargetsSiblingIsNotDerived(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "scope_parent", "example-client", "host", "api.example.com", []string{ActionHarmlessRequest}, nil, nil)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("notapi.example.com"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 0 {
		t.Fatalf("兄弟網域不該被推導，得到 %d 筆", len(derived))
	}
}

// TestDerivedTargetsDifferentDomainIsNotDerived：不同網域不可推導。
func TestDerivedTargetsDifferentDomainIsNotDerived(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "scope_parent", "example-client", "host", "api.example.com", []string{ActionHarmlessRequest}, nil, nil)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("api.example.com.evil.net"),
		NormalizeTarget("evil-example.com"),
		NormalizeTarget("other.example.net"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 0 {
		t.Fatalf("不同網域不該被推導，得到 %d 筆", len(derived))
	}
}

// TestDerivedTargetsIPInsideAuthorizedCIDR：授權網段內的位址可推導。
func TestDerivedTargetsIPInsideAuthorizedCIDR(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "scope_cidr", "example-client", "cidr", "10.20.0.0/24", []string{ActionHarmlessRequest}, nil, nil)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("10.20.0.7"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 1 {
		t.Fatalf("網段內位址應可推導，得到 %d 筆", len(derived))
	}
	if derived[0].SourceID != "scope_cidr" {
		t.Fatalf("來源應為 scope_cidr，得到 %q", derived[0].SourceID)
	}

	derived, err = svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("10.21.0.7"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 0 {
		t.Fatalf("網段外位址不該被推導，得到 %d 筆", len(derived))
	}
}

// TestDerivedTargetsIgnoresExpiredAuthorization：已過期的授權不可作為推導來源。
func TestDerivedTargetsIgnoresExpiredAuthorization(t *testing.T) {
	db := newScopeTestDB(t)
	expired := testNow.Add(-24 * time.Hour)
	insertTarget(t, db, "scope_expired", "example-client", "host", "api.example.com", []string{ActionHarmlessRequest}, nil, &expired)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("new.api.example.com"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 0 {
		t.Fatalf("已過期授權不該推導，得到 %d 筆", len(derived))
	}
}

// TestDerivedTargetsDoesNotDeriveFromSameHost：同一個主機是「涵蓋」不是「推導」。
func TestDerivedTargetsDoesNotDeriveFromSameHost(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "scope_same", "example-client", "host", "api.example.com", []string{ActionHarmlessRequest}, nil, nil)

	svc := NewService(db)
	derived, err := svc.DerivedTargets(context.Background(), []Target{
		NormalizeTarget("api.example.com"),
	}, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(derived) != 0 {
		t.Fatalf("同一主機不該算推導，得到 %d 筆", len(derived))
	}
}
