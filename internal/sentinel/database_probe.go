package sentinel

import (
	"bytes"
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"time"
)

// DatabaseEngineDef 定義數據庫探測項元數據
type DatabaseEngineDef struct {
	ID     string
	Name   string
	Ports  []int
	Method string
}

// AllDatabaseEngines 全部 30 類數據庫引擎定義
var AllDatabaseEngines = []DatabaseEngineDef{
	{ID: "elasticsearch", Name: "Elasticsearch", Ports: []int{9200}, Method: "HTTP GET / 识别 You Know, for Search"},
	{ID: "opensearch", Name: "OpenSearch", Ports: []int{9200}, Method: "HTTP GET / OpenSearch 横幅"},
	{ID: "es-transport", Name: "Elasticsearch Transport", Ports: []int{9300}, Method: "TCP 传输层连通"},
	{ID: "kibana", Name: "Kibana", Ports: []int{5601}, Method: "HTTP 控制台可达"},
	{ID: "mysql", Name: "MySQL / MariaDB", Ports: []int{3306, 3307}, Method: "TCP 握手版本串"},
	{ID: "sqlserver", Name: "SQL Server", Ports: []int{1433}, Method: "TDS PRELOGIN"},
	{ID: "db2", Name: "IBM DB2", Ports: []int{50000, 50001}, Method: "DRDA 横幅"},
	{ID: "mongodb", Name: "MongoDB", Ports: []int{27017, 27018}, Method: "isMaster 未授权探测"},
	{ID: "postgresql", Name: "PostgreSQL", Ports: []int{5432}, Method: "启动/SSL 握手"},
	{ID: "redis", Name: "Redis", Ports: []int{6379, 6380}, Method: "INFO / NOAUTH"},
	{ID: "oracle", Name: "Oracle", Ports: []int{1521}, Method: "TNS ping"},
	{ID: "couchdb", Name: "CouchDB", Ports: []int{5984}, Method: "HTTP Welcome JSON"},
	{ID: "cassandra", Name: "Cassandra", Ports: []int{9042}, Method: "CQL native OPTIONS"},
	{ID: "memcached", Name: "Memcached", Ports: []int{11211}, Method: "stats 未授权"},
	{ID: "clickhouse", Name: "ClickHouse", Ports: []int{8123}, Method: "HTTP /ping"},
	{ID: "influxdb", Name: "InfluxDB", Ports: []int{8086}, Method: "HTTP /ping"},
	{ID: "neo4j", Name: "Neo4j", Ports: []int{7474}, Method: "HTTP 发现接口"},
	{ID: "solr", Name: "Apache Solr", Ports: []int{8983}, Method: "HTTP /solr/"},
	{ID: "etcd", Name: "etcd", Ports: []int{2379}, Method: "HTTP /version"},
	{ID: "couchbase", Name: "Couchbase", Ports: []int{8091}, Method: "HTTP /pools"},
	{ID: "arangodb", Name: "ArangoDB", Ports: []int{8529}, Method: "HTTP /_api/version"},
	{ID: "rethinkdb", Name: "RethinkDB", Ports: []int{28015}, Method: "TCP 握手"},
	{ID: "firebird", Name: "Firebird", Ports: []int{3050}, Method: "TCP 横幅"},
	{ID: "tidb", Name: "TiDB", Ports: []int{4000}, Method: "MySQL 兼容握手"},
	{ID: "oceanbase", Name: "OceanBase", Ports: []int{2881}, Method: "握手横幅"},
	{ID: "kingbase", Name: "人大金仓 KingbaseES", Ports: []int{54321}, Method: "PostgreSQL 兼容握手"},
	{ID: "cockroachdb", Name: "CockroachDB", Ports: []int{26257}, Method: "PostgreSQL 兼容握手"},
	{ID: "hbase", Name: "Apache HBase", Ports: []int{16010}, Method: "HTTP /master-status"},
	{ID: "hive", Name: "Apache Hive", Ports: []int{10000}, Method: "HiveServer2 默认口"},
	{ID: "dameng", Name: "达梦 Dameng", Ports: []int{5236}, Method: "TCP 默认口 / 横幅"},
}

// ProbeDatabase 針對指定主機與端口執行非侵入式只讀數據庫探測
func ProbeDatabase(ctx context.Context, host string, port int) *DatabaseItem {
	target := net.JoinHostPort(host, fmt.Sprintf("%d", port))

	switch port {
	case 6379, 6380:
		return probeRedis(ctx, host, port, target)
	case 9200:
		return probeElasticsearch(ctx, host, port, target)
	case 9300:
		return probeESTransport(ctx, host, port, target)
	case 5601:
		return probeKibana(ctx, host, port, target)
	case 11211:
		return probeMemcached(ctx, host, port, target)
	case 27017, 27018:
		return probeMongoDB(ctx, host, port, target)
	case 3306, 3307:
		return probeMySQL(ctx, host, port, target, "mysql", "MySQL / MariaDB")
	case 4000:
		return probeMySQL(ctx, host, port, target, "tidb", "TiDB")
	case 2881:
		return probeMySQL(ctx, host, port, target, "oceanbase", "OceanBase")
	case 5432:
		return probePostgreSQL(ctx, host, port, target, "postgresql", "PostgreSQL")
	case 54321:
		return probePostgreSQL(ctx, host, port, target, "kingbase", "人大金仓 KingbaseES")
	case 26257:
		return probePostgreSQL(ctx, host, port, target, "cockroachdb", "CockroachDB")
	case 1433:
		return probeSQLServer(ctx, host, port, target)
	case 2379:
		return probeEtcd(ctx, host, port, target)
	case 5984:
		return probeCouchDB(ctx, host, port, target)
	case 8123:
		return probeClickHouse(ctx, host, port, target)
	case 8086:
		return probeInfluxDB(ctx, host, port, target)
	case 7474:
		return probeNeo4j(ctx, host, port, target)
	case 8983:
		return probeSolr(ctx, host, port, target)
	case 8091:
		return probeCouchbase(ctx, host, port, target)
	case 8529:
		return probeArangoDB(ctx, host, port, target)
	case 16010:
		return probeHBase(ctx, host, port, target)
	case 1521:
		return probeGenericTCP(ctx, host, port, target, "oracle", "Oracle", "Oracle TNS 端口開放")
	case 9042:
		return probeGenericTCP(ctx, host, port, target, "cassandra", "Cassandra", "Cassandra CQL 端口開放")
	case 28015:
		return probeGenericTCP(ctx, host, port, target, "rethinkdb", "RethinkDB", "RethinkDB 端口開放")
	case 3050:
		return probeGenericTCP(ctx, host, port, target, "firebird", "Firebird", "Firebird 端口開放")
	case 10000:
		return probeGenericTCP(ctx, host, port, target, "hive", "Apache Hive", "HiveServer2 端口開放")
	case 5236:
		return probeGenericTCP(ctx, host, port, target, "dameng", "达梦 Dameng", "达梦数据库端口開放")
	case 50000, 50001:
		return probeGenericTCP(ctx, host, port, target, "db2", "IBM DB2", "IBM DB2 DRDA 端口開放")
	default:
		return nil
	}
}

func probeRedis(ctx context.Context, host string, port int, target string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	_, err = conn.Write([]byte("INFO\r\n"))
	if err != nil {
		return nil
	}

	buf := make([]byte, 1024)
	n, err := conn.Read(buf)
	if err != nil && n == 0 {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "redis",
			EngineName: "Redis",
			Host:       host,
			Port:       port,
			Risk:       "open",
			Evidence:   "Redis 默認端口開放，但未響應 INFO",
		}
	}

	reply := string(buf[:n])
	if strings.Contains(reply, "redis_version") {
		ver := extractRedisVersion(reply)
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "redis",
			EngineName: "Redis",
			Host:       host,
			Port:       port,
			Risk:       "unauth",
			Evidence:   fmt.Sprintf("Redis 未授權訪問成功 (回顯版本: %s)", ver),
		}
	} else if strings.Contains(reply, "NOAUTH") {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "redis",
			EngineName: "Redis",
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   "Redis 服務暴露且受密碼保護 (回顯 -NOAUTH Authentication required)",
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   "redis",
		EngineName: "Redis",
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   "Redis 默認端口開放 (TCP 握手成功)",
	}
}

func extractRedisVersion(reply string) string {
	lines := strings.Split(reply, "\r\n")
	for _, l := range lines {
		if strings.HasPrefix(l, "redis_version:") {
			return strings.TrimPrefix(l, "redis_version:")
		}
	}
	return "未知"
}

func probeElasticsearch(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/", target)
	client := &http.Client{
		Timeout: 2 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
	bodyStr := string(body)

	if strings.Contains(bodyStr, "You Know, for Search") || strings.Contains(bodyStr, "cluster_name") {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "elasticsearch",
			EngineName: "Elasticsearch",
			Host:       host,
			Port:       port,
			Risk:       "unauth",
			Evidence:   "Elasticsearch REST API 未授權公開訪問 (命中 'You Know, for Search')",
		}
	} else if strings.Contains(strings.ToLower(bodyStr), "opensearch") {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "opensearch",
			EngineName: "OpenSearch",
			Host:       host,
			Port:       port,
			Risk:       "unauth",
			Evidence:   "OpenSearch REST API 未授權公開訪問",
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   "elasticsearch",
		EngineName: "Elasticsearch",
		Host:       host,
		Port:       port,
		Risk:       "identified",
		Evidence:   fmt.Sprintf("Elasticsearch 默認端口響應 HTTP %d", resp.StatusCode),
	}
}

func probeESTransport(ctx context.Context, host string, port int, target string) *DatabaseItem {
	return probeGenericTCP(ctx, host, port, target, "es-transport", "Elasticsearch Transport", "Elasticsearch 節點通信傳輸層端口開放")
}

func probeKibana(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/api/status", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "kibana",
			EngineName: "Kibana",
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   fmt.Sprintf("Kibana 控制台開放 (API 響應 HTTP %d)", resp.StatusCode),
		}
	}
	return nil
}

func probeMemcached(ctx context.Context, host string, port int, target string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	_, _ = conn.Write([]byte("stats\r\n"))
	buf := make([]byte, 512)
	n, err := conn.Read(buf)
	if err == nil && strings.Contains(string(buf[:n]), "STAT pid") {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "memcached",
			EngineName: "Memcached",
			Host:       host,
			Port:       port,
			Risk:       "unauth",
			Evidence:   "Memcached 緩存未授權訪問 (stats 命令執行成功)",
		}
	}
	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   "memcached",
		EngineName: "Memcached",
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   "Memcached 默認端口開放",
	}
}

func probeMongoDB(ctx context.Context, host string, port int, target string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	// 發送 OP_QUERY isMaster 包
	isMasterReq := []byte{
		0x3a, 0x00, 0x00, 0x00, // messageLength (58)
		0x01, 0x00, 0x00, 0x00, // requestID
		0x00, 0x00, 0x00, 0x00, // responseTo
		0xd4, 0x07, 0x00, 0x00, // opCode (2004 OP_QUERY)
		0x00, 0x00, 0x00, 0x00, // flags
		'a', 'd', 'm', 'i', 'n', '.', '$', 'c', 'm', 'd', 0x00, // fullCollectionName
		0x00, 0x00, 0x00, 0x00, // numberToSkip
		0xff, 0xff, 0xff, 0xff, // numberToReturn (-1)
		// query BSON: { "isMaster": 1 }
		0x13, 0x00, 0x00, 0x00,
		0x10, 'i', 's', 'M', 'a', 's', 't', 'e', 'r', 0x00,
		0x01, 0x00, 0x00, 0x00,
		0x00,
	}

	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	_, _ = conn.Write(isMasterReq)
	buf := make([]byte, 1024)
	n, err := conn.Read(buf)
	if err == nil && n > 20 {
		respStr := strings.ToLower(string(buf[:n]))
		if strings.Contains(respStr, "ismaster") || strings.Contains(respStr, "maxwireversion") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "mongodb",
				EngineName: "MongoDB",
				Host:       host,
				Port:       port,
				Risk:       "unauth",
				Evidence:   "MongoDB 未授權訪問 (isMaster 握手查詢成功)",
			}
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   "mongodb",
		EngineName: "MongoDB",
		Host:       host,
		Port:       port,
		Risk:       "identified",
		Evidence:   "MongoDB 服務默認端口握手可達",
	}
}

func probeMySQL(ctx context.Context, host string, port int, target, engineID, engineName string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	// 讀取 MySQL Greeting 數據包
	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	buf := make([]byte, 256)
	n, err := conn.Read(buf)
	if err == nil && n > 5 {
		// 第 4 字節為 protocol version (通常為 0x0a = 10)
		// 第 5 字節開始為 null-terminated 版本字符串
		nullIdx := bytes.IndexByte(buf[5:n], 0x00)
		ver := "未知"
		if nullIdx > 0 {
			ver = string(buf[5 : 5+nullIdx])
		}
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   engineID,
			EngineName: engineName,
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   fmt.Sprintf("%s 握手版本串暴露: %s", engineName, ver),
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   engineID,
		EngineName: engineName,
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   fmt.Sprintf("%s 端口開放", engineName),
	}
}

func probePostgreSQL(ctx context.Context, host string, port int, target, engineID, engineName string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	// 發送 SSLRequest: 00 00 00 08 04 d2 16 2f
	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	_, _ = conn.Write([]byte{0x00, 0x00, 0x00, 0x08, 0x04, 0xd2, 0x16, 0x2f})

	buf := make([]byte, 16)
	n, err := conn.Read(buf)
	if err == nil && n > 0 {
		if buf[0] == 'S' || buf[0] == 'N' {
			evidence := fmt.Sprintf("%s 握手成功 (SSL 響應: %c)", engineName, buf[0])
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   engineID,
				EngineName: engineName,
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   evidence,
			}
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   engineID,
		EngineName: engineName,
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   fmt.Sprintf("%s 端口開放", engineName),
	}
}

func probeSQLServer(ctx context.Context, host string, port int, target string) *DatabaseItem {
	d := net.Dialer{Timeout: 1500 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	// TDS Pre-login packet
	prelogin := []byte{
		0x12, 0x01, 0x00, 0x2f, 0x00, 0x00, 0x01, 0x00,
		0x00, 0x00, 0x1a, 0x00, 0x06, 0x01, 0x00, 0x20,
		0x00, 0x01, 0x02, 0x00, 0x21, 0x00, 0x01, 0x03,
		0x00, 0x22, 0x00, 0x00, 0x04, 0x00, 0x22, 0x00,
		0x01, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
		0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	}

	_ = conn.SetDeadline(time.Now().Add(1500 * time.Millisecond))
	_, _ = conn.Write(prelogin)
	buf := make([]byte, 256)
	n, err := conn.Read(buf)
	if err == nil && n > 8 && buf[0] == 0x04 {
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "sqlserver",
			EngineName: "SQL Server",
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   "SQL Server TDS PRELOGIN 握手成功",
		}
	}

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   "sqlserver",
		EngineName: "SQL Server",
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   "SQL Server 端口開放",
	}
}

func probeEtcd(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/version", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		if strings.Contains(string(body), "etcdserver") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "etcd",
				EngineName: "etcd",
				Host:       host,
				Port:       port,
				Risk:       "unauth",
				Evidence:   fmt.Sprintf("etcd 未授權讀取版本: %s", strings.TrimSpace(string(body))),
			}
		}
	}
	return nil
}

func probeCouchDB(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		if strings.Contains(string(body), "couchdb") && strings.Contains(string(body), "Welcome") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "couchdb",
				EngineName: "CouchDB",
				Host:       host,
				Port:       port,
				Risk:       "unauth",
				Evidence:   "CouchDB 默認歡迎接口未授權可訪問",
			}
		}
	}
	return nil
}

func probeClickHouse(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/ping", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 64))
		if strings.Contains(string(body), "Ok.") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "clickhouse",
				EngineName: "ClickHouse",
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   "ClickHouse HTTP /ping 接口響應 Ok.",
			}
		}
	}
	return nil
}

func probeInfluxDB(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/ping", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusNoContent || resp.StatusCode == http.StatusOK {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "influxdb",
				EngineName: "InfluxDB",
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   fmt.Sprintf("InfluxDB Ping 接口可達 (HTTP %d)", resp.StatusCode),
			}
		}
	}
	return nil
}

func probeNeo4j(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		if strings.Contains(string(body), "neo4j") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "neo4j",
				EngineName: "Neo4j",
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   "Neo4j HTTP 接口可達",
			}
		}
	}
	return nil
}

func probeSolr(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/solr/", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		if resp.StatusCode == 200 || resp.StatusCode == 403 || resp.StatusCode == 302 {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "solr",
				EngineName: "Apache Solr",
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   fmt.Sprintf("Apache Solr 控制台接口可達 (HTTP %d)", resp.StatusCode),
			}
		}
	}
	return nil
}

func probeCouchbase(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/pools", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "couchbase",
			EngineName: "Couchbase",
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   fmt.Sprintf("Couchbase REST API 可達 (HTTP %d)", resp.StatusCode),
		}
	}
	return nil
}

func probeArangoDB(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/_api/version", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 256))
		if strings.Contains(string(body), "server") {
			return &DatabaseItem{
				ID:         fmt.Sprintf("db-%s-%d", host, port),
				EngineID:   "arangodb",
				EngineName: "ArangoDB",
				Host:       host,
				Port:       port,
				Risk:       "identified",
				Evidence:   fmt.Sprintf("ArangoDB 版本接口可讀: %s", strings.TrimSpace(string(body))),
			}
		}
	}
	return nil
}

func probeHBase(ctx context.Context, host string, port int, target string) *DatabaseItem {
	url := fmt.Sprintf("http://%s/master-status", target)
	client := &http.Client{Timeout: 2 * time.Second}
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := client.Do(req)
	if err == nil {
		defer resp.Body.Close()
		return &DatabaseItem{
			ID:         fmt.Sprintf("db-%s-%d", host, port),
			EngineID:   "hbase",
			EngineName: "Apache HBase",
			Host:       host,
			Port:       port,
			Risk:       "identified",
			Evidence:   fmt.Sprintf("HBase Master Status 控制台可達 (HTTP %d)", resp.StatusCode),
		}
	}
	return nil
}

func probeGenericTCP(ctx context.Context, host string, port int, target, engineID, engineName, desc string) *DatabaseItem {
	d := net.Dialer{Timeout: 1200 * time.Millisecond}
	conn, err := d.DialContext(ctx, "tcp", target)
	if err != nil {
		return nil
	}
	defer conn.Close()

	return &DatabaseItem{
		ID:         fmt.Sprintf("db-%s-%d", host, port),
		EngineID:   engineID,
		EngineName: engineName,
		Host:       host,
		Port:       port,
		Risk:       "open",
		Evidence:   desc,
	}
}
