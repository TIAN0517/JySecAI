package logger

import (
	"io"
	"os"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

type Logger struct {
	*zap.Logger
	// closer 非 nil 代表 New 自己開了日誌檔案，Close 才需要（也才可以）關它。
	// stdout/stderr 不歸這個 Logger 所有，關掉會影響同行程的其他寫入者。
	closer io.Closer
}

// Close 關閉由 New 開啟的日誌檔案。
//
// zap.Logger.Sync() 只做 flush 不做 close，檔案句會一直開著。Linux 允許刪除
// 開啟中的檔案所以看不出問題，但 Windows 不允許，測試用 t.TempDir() 清理時
// 會直接失敗；服務關機時也會留下句柄。輸出到 stdout/stderr 或開檔失敗
// （此時已退回 stdout）時為 no-op。可重複呼叫。
func (l *Logger) Close() error {
	if l == nil || l.closer == nil {
		return nil
	}
	err := l.closer.Close()
	l.closer = nil
	return err
}

func New(level, output string, diagnostics ...DiagnosticOptions) *Logger {
	var zapLevel zapcore.Level
	switch level {
	case "debug":
		zapLevel = zapcore.DebugLevel
	case "info":
		zapLevel = zapcore.InfoLevel
	case "warn":
		zapLevel = zapcore.WarnLevel
	case "error":
		zapLevel = zapcore.ErrorLevel
	default:
		zapLevel = zapcore.InfoLevel
	}

	config := zap.NewProductionConfig()
	config.Level = zap.NewAtomicLevelAt(zapLevel)
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	var writeSyncer zapcore.WriteSyncer
	var closer io.Closer
	if output == "stdout" {
		writeSyncer = zapcore.AddSync(os.Stdout)
	} else if output == "stderr" {
		writeSyncer = zapcore.AddSync(os.Stderr)
	} else {
		file, err := os.OpenFile(output, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			writeSyncer = zapcore.AddSync(os.Stdout)
		} else {
			writeSyncer = zapcore.AddSync(file)
			closer = file
		}
	}

	core := zapcore.NewCore(
		newS2TEncoder(zapcore.NewJSONEncoder(config.EncoderConfig)),
		writeSyncer,
		zapLevel,
	)

	options := DiagnosticOptions{}
	if len(diagnostics) > 0 {
		options = diagnostics[0]
	}
	if !options.Disabled {
		// The diagnostic threshold is independent of the primary output level.
		core = zapcore.NewTee(core, zapcore.NewCore(
			newS2TEncoder(zapcore.NewJSONEncoder(config.EncoderConfig)),
			newDailyWriter(options), zapcore.WarnLevel,
		))
	}

	logger := zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))

	return &Logger{Logger: logger, closer: closer}
}

func (l *Logger) Fatal(msg string, fields ...interface{}) {
	zapFields := make([]zap.Field, 0, len(fields))
	for _, f := range fields {
		switch v := f.(type) {
		case error:
			zapFields = append(zapFields, zap.Error(v))
		default:
			zapFields = append(zapFields, zap.Any("field", v))
		}
	}
	l.Logger.Fatal(msg, zapFields...)
}
