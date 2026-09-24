package app

import (
	"context"
	"go.uber.org/zap"
	"jysecai/internal/config"
	"net"
	"testing"
)

func TestXSSAppCollectorDisabledAndBindFailure(t *testing.T) {
	c, err := startXSSCollector(nil, config.XssConfig{Enabled: false}, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	if c.Addr() != "" {
		t.Fatal("disabled collector opened listener")
	}
	if err = c.Stop(context.Background()); err != nil {
		t.Fatal(err)
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()
	if _, err = startXSSCollector(nil, config.XssConfig{Enabled: true, BindHost: "127.0.0.1", BindPort: ln.Addr().(*net.TCPAddr).Port}, zap.NewNop()); err == nil {
		t.Fatal("bind failure swallowed")
	}
}
