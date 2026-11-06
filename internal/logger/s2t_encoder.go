package logger

import (
	"time"

	"go.uber.org/zap/buffer"
	"go.uber.org/zap/zapcore"

	"jysecai/internal/logger/zhconv"
)

// s2tEncoder 包住既有的 zapcore.Encoder,
// 在寫入 "msg" 欄位時自動將簡體中文轉為繁體中文。
// 其餘欄位(caller/timestamp/field)不經手,維持原有行為。
//
// 這是純輸出層裝飾:不影響 log 結構、不影響欄位數值,
// 只改動最終顯示的文字。停用時換掉 logger.New 裡的
// newS2TEncoder 呼叫即可回到原始 encoder。
type s2tEncoder struct {
	inner zapcore.Encoder
}

func newS2TEncoder(inner zapcore.Encoder) zapcore.Encoder {
	return &s2tEncoder{inner: inner}
}

func (e *s2tEncoder) AddArray(key string, v zapcore.ArrayMarshaler) error {
	return e.inner.AddArray(key, v)
}
func (e *s2tEncoder) AddObject(key string, v zapcore.ObjectMarshaler) error {
	return e.inner.AddObject(key, v)
}
func (e *s2tEncoder) AddBinary(key string, value []byte) {
	e.inner.AddBinary(key, value)
}
func (e *s2tEncoder) AddByteString(key string, value []byte) {
	e.inner.AddByteString(key, value)
}
func (e *s2tEncoder) AddBool(key string, value bool) {
	e.inner.AddBool(key, value)
}
func (e *s2tEncoder) AddComplex128(key string, value complex128) {
	e.inner.AddComplex128(key, value)
}
func (e *s2tEncoder) AddComplex64(key string, value complex64) {
	e.inner.AddComplex64(key, value)
}
func (e *s2tEncoder) AddDuration(key string, value time.Duration) {
	e.inner.AddDuration(key, value)
}
func (e *s2tEncoder) AddFloat64(key string, value float64) {
	e.inner.AddFloat64(key, value)
}
func (e *s2tEncoder) AddFloat32(key string, value float32) {
	e.inner.AddFloat32(key, value)
}
func (e *s2tEncoder) AddInt(key string, value int) {
	e.inner.AddInt(key, value)
}
func (e *s2tEncoder) AddInt64(key string, value int64) {
	e.inner.AddInt64(key, value)
}
func (e *s2tEncoder) AddInt32(key string, value int32) {
	e.inner.AddInt32(key, value)
}
func (e *s2tEncoder) AddInt16(key string, value int16) {
	e.inner.AddInt16(key, value)
}
func (e *s2tEncoder) AddInt8(key string, value int8) {
	e.inner.AddInt8(key, value)
}

// AddString 是唯一被攔截的欄位:zap 把 log message 以此方法寫入 key="msg"。
func (e *s2tEncoder) AddString(key, value string) {
	if key == "msg" {
		value = zhconv.S2T(value)
	}
	e.inner.AddString(key, value)
}

func (e *s2tEncoder) AddTime(key string, value time.Time) {
	e.inner.AddTime(key, value)
}
func (e *s2tEncoder) AddUint(key string, value uint) {
	e.inner.AddUint(key, value)
}
func (e *s2tEncoder) AddUint64(key string, value uint64) {
	e.inner.AddUint64(key, value)
}
func (e *s2tEncoder) AddUint32(key string, value uint32) {
	e.inner.AddUint32(key, value)
}
func (e *s2tEncoder) AddUint16(key string, value uint16) {
	e.inner.AddUint16(key, value)
}
func (e *s2tEncoder) AddUint8(key string, value uint8) {
	e.inner.AddUint8(key, value)
}
func (e *s2tEncoder) AddUintptr(key string, value uintptr) {
	e.inner.AddUintptr(key, value)
}

func (e *s2tEncoder) AddReflected(key string, value interface{}) error {
	return e.inner.AddReflected(key, value)
}
func (e *s2tEncoder) OpenNamespace(key string) {
	e.inner.OpenNamespace(key)
}
func (e *s2tEncoder) Clone() zapcore.Encoder {
	return &s2tEncoder{inner: e.inner.Clone()}
}
func (e *s2tEncoder) EncodeEntry(ent zapcore.Entry, fields []zapcore.Field) (*buffer.Buffer, error) {
	ent.Message = zhconv.S2T(ent.Message)
	return e.inner.EncodeEntry(ent, fields)
}
