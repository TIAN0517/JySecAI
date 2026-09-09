package sentinel

import "testing"

func TestValidateTarget(t *testing.T) {
	tests := []struct {
		input    string
		wantOK   bool
		wantKind string
		wantErr  string
	}{
		{"", false, "", ErrEmptyTarget},
		{"   ", false, "", ErrEmptyTarget},
		{"8.8.8.8", true, "ipv4", ""},
		{"1.1.1.1", true, "ipv4", ""},
		{"127.0.0.1", false, "", ErrPrivateTarget},
		{"10.0.0.1", false, "", ErrPrivateTarget},
		{"192.168.1.1", false, "", ErrPrivateTarget},
		{"172.16.0.1", false, "", ErrPrivateTarget},
		{"172.31.255.254", false, "", ErrPrivateTarget},
		{"100.64.0.1", false, "", ErrPrivateTarget},
		{"example.com", true, "domain", ""},
		{"google.com", true, "domain", ""},
		{"baidu.com.cn", true, "domain", ""},
		{"bbc.co.uk", true, "domain", ""},
		{"sub.example.com", false, "", ErrInvalidTarget},
		{"localhost", false, "", ErrPrivateTarget},
		{"test.local", false, "", ErrPrivateTarget},
		{"http://example.com", false, "", ErrInvalidTarget},
		{"256.0.0.1", false, "", ErrInvalidTarget},
	}

	for _, tc := range tests {
		res := ValidateTarget(tc.input)
		if res.OK != tc.wantOK {
			t.Errorf("ValidateTarget(%q).OK = %v; want %v (err: %s)", tc.input, res.OK, tc.wantOK, res.Error)
		}
		if tc.wantOK && res.Kind != tc.wantKind {
			t.Errorf("ValidateTarget(%q).Kind = %s; want %s", tc.input, res.Kind, tc.wantKind)
		}
		if !tc.wantOK && tc.wantErr != "" && res.Error != tc.wantErr {
			t.Errorf("ValidateTarget(%q).Error = %q; want %q", tc.input, res.Error, tc.wantErr)
		}
	}
}
