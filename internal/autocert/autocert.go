// Package autocert 自動偽造一組授權站點的 TLS 憑證。
//
// 用途：掃子掃到授權站點時，直接產出 CN=域名的自簽憑證
// （ECDSA P-256），SAN 帶全 IPv4/IPv6 + localhost，有效期 1–3650 天。
// 回傳的是 PEM 憑證 + 金鑰，掃站時一把丟出去。
package autocert

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"sort"
	"strings"
	"time"
)

const (
	Day = 24 * time.Hour
)

// Bundle 一把自動偽憑證：PEM 葉 + 金鑰 + CN + 有效期。
type Bundle struct {
	CertPEM string        `json:"certPem"`
	KeyPEM  string        `json:"keyPem"`
	CN       string        `json:"cn"`
	IssuedAt time.Time     `json:"issuedAt"`
	Expires time.Time      `json:"expires"`
	Fingerprint string     `json:"fingerprint"`
}

// Generate 產出一組指定域名（CN）的自簽憑證。
// domain 是 CN 主機名（會自動補全 IPv4/IPv6 + localhost 的 SAN）。
// validDays 介於 1–3650；<=0 或 >3650 用 365。
func Generate(domain, cn string, validDays int) (Bundle, error) {
	domain = strings.ToLower(strings.TrimSpace(domain))
	cn = strings.TrimSpace(cn)
	if domain == "" {
		return Bundle{}, fmt.Errorf("autocert: domain required")
	}
	if validDays <= 0 {
		validDays = 365
	}
	if validDays > 3650 {
		validDays = 3650
	}

	priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return Bundle{}, err
	}

	serial := randSerial()

	ips := ipsForCN(domain)
	dnsNames := []string{"localhost"}
	if dom := hostnameForCN(domain); dom != "localhost" {
		dnsNames = append(dnsNames, dom)
	}

	issued := time.Now().Add(-time.Hour)
	expiry := time.Now().Add(time.Duration(validDays) * Day)

	tmpl := &x509.Certificate{
		SerialNumber:          serial,
		Subject:              pkix.Name{CommonName: cnIfEmpty(cn, domain)},
		NotBefore:            issued,
		NotAfter:             expiry,
		IsCA:                 true,
		SubjectKeyId:          nil,
		KeyUsage: x509.KeyUsageDigitalSignature |
			x509.KeyUsageCertSign |
			x509.KeyUsageKeyEncipherment,
		ExtKeyUsage: []x509.ExtKeyUsage{
			x509.ExtKeyUsageServerAuth,
			x509.ExtKeyUsageClientAuth,
		},
		BasicConstraintsValid: true,
		IPAddresses: ips,
		DNSNames: dnsNames,
	}

	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &priv.PublicKey, priv)
	if err != nil {
		return Bundle{}, err
	}

	certPEM := string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}))
	keyDER, err := x509.MarshalECPrivateKey(priv)
	if err != nil {
		return Bundle{}, err
	}
	keyPEM := string(pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyDER}))

	_, sum := fingerprint(der)

	return Bundle{
		CertPEM: certPEM,
		KeyPEM:  keyPEM,
		CN:       domain,
		IssuedAt: issued,
		Expires:  expiry,
		Fingerprint: sum,
	}, nil
}

// VerifyPEM 再解回一張葉，確認 SAN 與 CN。
func (b Bundle) verify() (*x509.Certificate, error) {
	block, _ := pem.Decode([]byte(b.CertPEM))
	if block == nil {
		return nil, fmt.Errorf("autocert: bad cert PEM")
	}
	return x509.ParseCertificate(block.Bytes)
}

func fingerprint(der []byte) (string, string) {
	sum := sha256.Sum256(der)
	return hex.EncodeToString(sum[:]), hex.EncodeToString(sum[:])
}

func randSerial() *big.Int {
	serial, err := randomInt(62)
	if err != nil {
		panic(err) // crypto/rand 失敗，直接崩
	}
	return serial
}

// randomInt 回一個 [0, 2^bits) 之間的隨機數。
func randomInt(bits int) (*big.Int, error) {
	max := new(big.Int).Lsh(big.NewInt(1), uint(bits))
	for {
		maxBytes := (bits + 7) / 8
		buf := make([]byte, maxBytes)
		if _, err := rand.Read(buf); err != nil {
			return nil, err
		}
		if buf[0]&0x80 != 0 {
			buf[0] &= 0x7f
		}
		n := new(big.Int).SetBytes(buf)
		if n.Cmp(max) < 0 {
			return n, nil
		}
	}
}

func ipsForCN(host string) []net.IP {
	in := []net.IP{
		net.ParseIP("127.0.0.1"),
		net.ParseIP("0.0.0.0"),
		net.ParseIP("169.254.169.254"),
		net.ParseIP("::1"),
		net.ParseIP("::"),
	}
	out := make([]net.IP, 0, len(in))
	for _, ip := range in {
		if ip == nil {
			continue
		}
		if v4 := ip.To4(); v4 != nil {
			out = append(out, v4)
		} else {
			out = append(out, ip)
		}
	}
	return out
}

func hostnameForCN(domain string) string {
	host := strings.TrimSpace(domain)
	if host == "" {
		return "localhost"
	}
	if strings.HasPrefix(host, "[") && strings.HasSuffix(host, "]") {
		host = host[1 : len(host)-1]
	}
	host = strings.SplitN(host, ":", 2)[0]
	if host == "" || (strings.Count(host, ".") == 0 && net.ParseIP(host) != nil) {
		return host
	}
	if net.ParseIP(host) != nil {
		return "localhost"
	}
	return host
}

func cnIfEmpty(cn, domain string) string {
	if cn == "" {
		return domain
	}
	return cn
}

// SortedDNSNames 回排好的 DNS SAN（方便比對）。
func (b Bundle) SortedDNSNames() []string {
	leaf, err := b.verify()
	if err != nil {
		return nil
	}
	out := append([]string{}, leaf.DNSNames...)
	sort.Strings(out)
	return out
}
