package c2

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
)

// 这些薄封装存在的目的：
//   - 让 manager.go / handler 中的逻辑更直观，避免反复 import os；
//   - 便于将来用接口抽象（譬如改成 internal/storage 的实现）做单元测试。

func osMkdirAll(path string, perm os.FileMode) error {
	return os.MkdirAll(path, perm)
}

func osWriteFile(path string, data []byte, perm os.FileMode) error {
	return os.WriteFile(path, data, perm)
}

func base64Decode(s string) ([]byte, error) {
	return base64.StdEncoding.DecodeString(s)
}

// ensureNoSymlinkEscape 檢查「寫入 dir 內的 path」不會經由符號連結落到別處。
//
// 為什麼字面檢查不夠：ensurePathInDir 用的是 filepath.Abs + filepath.Rel，
// 純粹比較字串。攻擊者若能在結果目錄放置符號連結，os.WriteFile 會跟著穿透，
// 把內容寫到 dir 之外 —— 這種情況字面檢查完全看不到。
//
// 兩個方向都要擋：
//  1. dir 本身被換成指向別處的符號連結（此時所有寫入都會逃逸）。
//  2. path 已存在且是符號連結（此時該次寫入會跟著穿透）。
//
// 回傳錯誤而非靜默修正：呼叫端需要把這種狀況記錄下來，而不是假裝寫入成功。
func ensureNoSymlinkEscape(dir, path string) error {
	// 方向 1：目錄本身不得是符號連結。
	// 用 os.SameFile 比對身分而非字串，Windows 上大小寫與 8.3 短路徑的
	// 表示差異不會造成誤判。
	if resolved, err := filepath.EvalSymlinks(dir); err == nil {
		linkInfo, lerr := os.Lstat(dir)
		targetInfo, terr := os.Stat(resolved)
		if lerr == nil && terr == nil && !os.SameFile(linkInfo, targetInfo) {
			return fmt.Errorf("拒绝写入符号链接目录: %s -> %s", dir, resolved)
		}
	} else if !os.IsNotExist(err) {
		// 解析失敗且不是「不存在」：寧可保守擋下，也不要在未知狀態下寫入。
		return fmt.Errorf("无法解析结果目录: %w", err)
	}

	// 方向 2：目標不得是既有的符號連結。
	if info, err := os.Lstat(path); err == nil {
		if info.Mode()&os.ModeSymlink != 0 {
			return fmt.Errorf("拒绝透过符号链接写入: %s", path)
		}
	} else if !os.IsNotExist(err) {
		return fmt.Errorf("无法检查目标路径: %w", err)
	}
	return nil
}
