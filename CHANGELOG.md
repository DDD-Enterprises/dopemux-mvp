# Changelog
All notable changes will be documented in this file.

## [Unreleased] - 2025-09-26

### Security
- **CRITICAL**: Fix dangerous mode security vulnerabilities with time-limited sessions and explicit user consent
- **HIGH**: Add file path validation to prevent directory traversal attacks
- **HIGH**: Implement secure subprocess execution with command whitelisting for git operations
- **MEDIUM**: Add environment variable protection to prevent API key exposure in logs
- **LOW**: Harden shell scripts with dynamic date handling and robust import management

### Added
- Time-limited dangerous mode with 1-hour automatic expiry
- Comprehensive file path boundary validation
- Secure git command runner with timeout protection
- Sensitive data detection and sanitization for logging
- Visual security warnings with ADHD-friendly UI design
- Security audit trail logging without sensitive data exposure

### Changed
- Dangerous mode now requires double confirmation with clear risk warnings
- All file operations now validate paths within project boundaries
- Git operations use whitelisted commands with input sanitization
- Environment variables automatically redacted in logs if sensitive
- Shell scripts use dynamic dates instead of hard-coded values

### Security Model
- Implemented layered defense with input validation at all entry points
- Added fail-safe defaults ensuring secure-by-default operations
- Enhanced audit trail with security event logging
- Cognitive load management for ADHD users with gentle security UX

See `SECURITY_FIXES_2025-09-26.md` for detailed security documentation.
