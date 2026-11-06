package handler

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"
)

func TestTaskDeadlineExceededContextOwnership(t *testing.T) {
	taskCtx, stop := context.WithTimeout(context.Background(), 10*time.Hour)
	defer stop()
	child, stopChild := context.WithDeadline(taskCtx, time.Now().Add(-time.Second))
	defer stopChild()
	if !errors.Is(child.Err(), context.DeadlineExceeded) {
		t.Fatal("child deadline did not expire")
	}
	if taskDeadlineExceeded(taskCtx) {
		t.Fatal("child expiry exhausted parent task")
	}
	if !taskDeadlineExceeded(child) {
		t.Fatal("expired task deadline not recognized")
	}

	cancelled, cancel := context.WithCancelCause(context.Background())
	cancel(fmt.Errorf("child failed: %w", context.DeadlineExceeded))
	if taskDeadlineExceeded(cancelled) {
		t.Fatal("cancellation cause misclassified as task deadline")
	}

	userCtx, userCancel := context.WithCancelCause(context.Background())
	userCancel(ErrTaskCancelled)
	defer userCancel(ErrTaskCancelled)
	if taskDeadlineExceeded(userCtx) {
		t.Fatal("user cancellation misclassified as task deadline")
	}

	customDeadline, stopCustom := context.WithDeadlineCause(context.Background(), time.Now().Add(-time.Second), errors.New("budget exhausted"))
	defer stopCustom()
	if !taskDeadlineExceeded(customDeadline) {
		t.Fatal("custom deadline cause hid real task expiry")
	}
	if taskDeadlineExceeded(nil) || taskDeadlineExceeded(context.Background()) {
		t.Fatal("context without deadline classified as expired")
	}
}
