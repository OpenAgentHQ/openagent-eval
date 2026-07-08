# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x | Yes |

## Reporting a Vulnerability

If you discover a security vulnerability within OpenAgent Eval, please send an email to security@openagenthq.com. All security vulnerabilities will be promptly addressed.

**Do NOT report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Released**: Within 30 days (for critical issues)

### What to Expect

1. We will acknowledge receipt of your report
2. We will confirm the vulnerability and determine its impact
3. We will develop a fix
4. We will release the fix
5. We will publicly disclose the vulnerability (after fix is released)

## Security Update Process

### For Users

When a security update is released:
1. Update to the latest version
2. Review the changelog for security fixes
3. Test your application
4. Deploy the update

### For Maintainers

When a security issue is reported:
1. Acknowledge the report
2. Assess the severity
3. Develop a fix
4. Test the fix
5. Release the update
6. Update the changelog
7. Notify users

## Security Best Practices

### For Users

- Keep dependencies up to date
- Use environment variables for API keys and secrets (never hardcode them)
- Validate all configuration inputs
- Use HTTPS when connecting to external LLM providers
- Enable security features provided by your OS and Python

### For Contributors

- Follow secure coding practices
- Validate input at boundaries
- Use parameterized queries where applicable
- Sanitize output
- Handle errors securely
- Never commit secrets or API keys
- Use `.env` files for local development secrets

## Contact

For security-related questions or concerns, please contact:
- **Email**: security@openagenthq.com

## Acknowledgments

We would like to thank the following researchers for responsibly disclosing vulnerabilities:
- (None yet)

---

Thank you for helping keep OpenAgent Eval and its users safe.
