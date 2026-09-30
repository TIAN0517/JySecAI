# Government Portal Testing Patterns

## Default Routing Detection (0.0.0.0 Catch-All)

Government portals often implement default catch-all routing that returns the same frontend page for all unknown paths.

**Detection Pattern:**
```
Status codes: 200 for ALL paths (login, admin, api, user, config, backups)
Content: Identical HTML with same content length (±2% variance)
Headers: Same cache headers across all paths
```

**Identification Method:**
```bash
# Test multiple paths with same session
paths=("/admin" "/api/v1" "/user/1" "/config" "/backup")
for path in "${paths[@]}"; do
  status=$(curl -k -s -o /dev/null -w "%{http_code}" "URL${path}")
  len=$(curl -k -s "URL${path}" | wc -c)
  echo "${path}: ${status} ${len}"
done
# Result: All 200 with similar lengths = default routing
```

## Impact on Testing

When default routing is detected:
1. Directory brute-forcing is NOT effective (all return 200)
2. File discovery tools (like gobuster) produce false positives
3. API endpoint enumeration returns empty pages
4. Admin panels may not exist or are completely separate

**Alternative approaches:**
- Check source code archives (/.git, /composer.json, /package.json)
- Look for hidden form actions in HTML
- Examine JavaScript bundles for API endpoints
- Test for IDOR on any exposed user data endpoints
- Check for configuration files with actual content vs empty pages

## Common Patterns in Government Portals

### Frontend Payment Query Systems
- **URL Pattern**: /admin/login, /showList
- **Function**: Citizen payment history lookup
- **Admin Panel**: Often just a search interface, no comprehensive backend
- **Valid Endpoints**: Only specific POST endpoints return data

### Session Characteristics
- Shorter session timeout (1-2 hours typically)
- CSRF token validation on all POST requests
- Session invalidation on form timeout (419 error)

### Captcha Systems
- SVG-based captchas with visible text (easy OCR)
- Regex extract: `<text[^>]*>(\w)</text>` 
- Often: single character or short alphanumeric string