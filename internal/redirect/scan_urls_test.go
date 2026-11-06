package redirect

import (
	"reflect"
	"testing"
)

func TestExtractHTTPURLs(t *testing.T) {
	text := "扫 https://victim.example/login?next=/home 以及 http://a.test/go。短链 https://97y.me/tjneJ 不要当目标。"
	got := ExtractHTTPURLs(text)
	want := []string{
		"https://victim.example/login?next=/home",
		"http://a.test/go",
		"https://97y.me/tjneJ",
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("ExtractHTTPURLs = %#v, want %#v", got, want)
	}
}

func TestFilterOwnCallbackURLs(t *testing.T) {
	seeds := []string{
		"https://victim.example/login",
		"https://97y.me/tjneJ",
		"http://a.test/go",
	}
	got := FilterOwnCallbackURLs(seeds, []string{"97y.me"})
	want := []string{"https://victim.example/login", "http://a.test/go"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("FilterOwnCallbackURLs = %#v, want %#v", got, want)
	}
}
