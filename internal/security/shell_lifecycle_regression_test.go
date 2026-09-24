package security

import (
	"fmt"
	"testing"
)

func TestRaceRegression_ConcurrentBlockedStdinLifecycles(t *testing.T) {
	// Exercise four independent startup/wait/kill lifecycles concurrently using
	// the existing negative control. Each invocation must join its child.
	for i := 0; i < 4; i++ {
		t.Run(fmt.Sprint(i), func(t *testing.T) {
			t.Parallel()
			TestNonInteractiveStdinReadBlocksWithoutRedirect(t)
		})
	}
}
