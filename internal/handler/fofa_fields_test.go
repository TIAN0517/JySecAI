package handler

import "testing"

func TestNormalizeFofaFields(t *testing.T) {
	got := normalizeFofaFields(" host, province, region, city, province,host ")
	if got != "host,region,city" {
		t.Fatalf("got %q", got)
	}
	if normalizeFofaFields("country,province,city") != "country,region,city" {
		t.Fatal("legacy province was not rewritten")
	}
}
