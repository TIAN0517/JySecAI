package c2

import "testing"

func TestDangerousTaskTypesCoverSideEffects(t *testing.T) {
	for _, taskType := range []TaskType{
		TaskTypeExec, TaskTypeShell, TaskTypeCd, TaskTypeKillProc,
		TaskTypeUpload, TaskTypeDownload, TaskTypeScreenshot, TaskTypeSleep,
		TaskTypeExit, TaskTypeSelfDelete, TaskTypePortFwd, TaskTypeSocksStart,
		TaskTypeSocksStop, TaskTypeLoadAssembly, TaskTypePersist,
	} {
		if !IsDangerousTaskType(taskType) {
			t.Errorf("task type %q should require HITL when the gate is enabled", taskType)
		}
	}
	for _, readOnly := range []TaskType{TaskTypePwd, TaskTypeLs, TaskTypePs} {
		if IsDangerousTaskType(readOnly) {
			t.Errorf("read-only task type %q should not be marked dangerous", readOnly)
		}
	}
}
