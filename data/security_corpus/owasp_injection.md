# OWASP — Injection (A03:2021)

Injection flaws occur when untrusted data is sent to an interpreter as part of a command or query.

## SQL Injection

Attackers can manipulate queries by injecting SQL syntax. Use parameterized queries / prepared statements and avoid string concatenation for SQL.

## Command Injection

Avoid passing user-controlled strings to operating system shells. Prefer subprocess with argument lists and never `shell=True` with untrusted input.

## LDAP / XPath / NoSQL

Apply the same principle: separate structure from data and validate/escape appropriately.
