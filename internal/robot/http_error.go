package robot

import (
	"errors"
	"fmt"
	"net/url"
)

// safeRobotHTTPError removes request URLs before an error reaches logs. Some
// robot APIs place bot tokens or client secrets in the URL path/query.
func safeRobotHTTPError(operation string, err error) error {
	if err == nil {
		return nil
	}
	var urlErr *url.Error
	if errors.As(err, &urlErr) {
		if urlErr.Err != nil {
			return fmt.Errorf("%s: %w", operation, urlErr.Err)
		}
		return fmt.Errorf("%s request failed", operation)
	}
	return fmt.Errorf("%s: %w", operation, err)
}
