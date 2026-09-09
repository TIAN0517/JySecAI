package sentinel

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"sync"
	"time"
)

var defaultTargetPorts = []int{
	// 基礎 Web 端口
	80, 443, 8080, 8443, 8000, 8888, 9000, 3000, 5000, 8081,
	// 數據庫默認端口（30 類覆蓋）
	9200, 9300, 5601, 3306, 3307, 1433, 27017, 27018, 5432, 6379, 6380,
	1521, 5984, 9042, 11211, 8123, 8086, 7474, 8983, 2379, 8091, 8529,
	28015, 3050, 4000, 2881, 54321, 26257, 16010, 10000, 5236, 50000, 50001,
	// 常見運維與服務端口
	21, 22, 23, 25, 110, 143, 873, 3389, 5900, 6443, 2375,
}

var portServiceNameMap = map[int]string{
	80: "HTTP", 443: "HTTPS", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 8000: "HTTP-Alt",
	8888: "HTTP-Alt", 9000: "HTTP/FastCGI", 3000: "Node/Dev", 5000: "Dev-Web", 8081: "HTTP-Alt",
	9200: "Elasticsearch", 9300: "ES-Transport", 5601: "Kibana", 3306: "MySQL", 3307: "MySQL-Alt",
	1433: "MSSQL", 27017: "MongoDB", 27018: "MongoDB-Alt", 5432: "PostgreSQL", 6379: "Redis", 6380: "Redis-TLS",
	1521: "Oracle", 5984: "CouchDB", 9042: "Cassandra", 11211: "Memcached", 8123: "ClickHouse",
	8086: "InfluxDB", 7474: "Neo4j", 8983: "Solr", 2379: "etcd", 8091: "Couchbase", 8529: "ArangoDB",
	28015: "RethinkDB", 3050: "Firebird", 4000: "TiDB", 2881: "OceanBase", 54321: "Kingbase",
	26257: "CockroachDB", 16010: "HBase", 10000: "Hive", 5236: "Dameng", 50000: "DB2", 50001: "DB2-Alt",
	21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 110: "POP3", 143: "IMAP", 873: "Rsync",
	3389: "RDP", 5900: "VNC", 6443: "K8s-API", 2375: "Docker",
}

// ScanPortsAndTLS 對指定主機執行快速並發端口連通性掃描並校驗 TLS 證書
func ScanPortsAndTLS(ctx context.Context, host string, ip string) ([]PortItem, bool) {
	connectTarget := host
	if ip != "" {
		connectTarget = ip
	}

	type portRes struct {
		port    int
		open    bool
		service string
	}

	resChan := make(chan portRes, len(defaultTargetPorts))
	sem := make(chan struct{}, 25) // 25 並發
	var wg sync.WaitGroup

	for _, p := range defaultTargetPorts {
		wg.Add(1)
		go func(port int) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			addr := net.JoinHostPort(connectTarget, fmt.Sprintf("%d", port))
			d := net.Dialer{Timeout: 1200 * time.Millisecond}
			conn, err := d.DialContext(ctx, "tcp", addr)
			if err == nil {
				_ = conn.Close()
				svc := portServiceNameMap[port]
				if svc == "" {
					svc = "TCP"
				}
				resChan <- portRes{port: port, open: true, service: svc}
			}
		}(p)
	}

	wg.Wait()
	close(resChan)

	var items []PortItem
	idx := 0
	has443 := false

	for res := range resChan {
		idx++
		if res.port == 443 {
			has443 = true
		}
		items = append(items, PortItem{
			ID:      fmt.Sprintf("port-%s-%d", host, res.port),
			Host:    host,
			IP:      ip,
			Port:    res.port,
			Service: res.service,
		})
	}

	// 校驗 TLS 證書（若 443 開放，做 TLS 握手校驗證書有效性）
	tlsValid := false
	if has443 {
		conf := &tls.Config{
			ServerName: host,
			// 嚴格驗證以判斷證書是否有效
			InsecureSkipVerify: false,
		}
		dialer := &net.Dialer{Timeout: 2 * time.Second}
		tlsConn, err := tls.DialWithDialer(dialer, "tcp", net.JoinHostPort(connectTarget, "443"), conf)
		if err == nil {
			tlsValid = true
			_ = tlsConn.Close()
		}
	}

	return items, tlsValid
}
