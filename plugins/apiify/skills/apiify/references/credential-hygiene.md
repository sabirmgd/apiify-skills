# Credential Hygiene

Do not ask users to paste real passwords into chat. Do not include credentials in commands shown in the transcript.

Preferred auth paths:

1. Headed browser login controlled by the user.
2. Local `.env` file read by the generated script.
3. Browser state or cookie file created locally.
4. One-time throwaway credentials when the user explicitly accepts the risk.

## Redaction

Redact these from logs, metadata, and examples:

- passwords;
- bearer tokens;
- cookies and session IDs;
- CSRF tokens;
- API keys;
- account IDs if they identify a private account.

Use placeholders like:

```text
<REDACTED_SESSION_COOKIE>
<REDACTED_BEARER_TOKEN>
```

## Shell History

Avoid commands like:

```bash
PASSWORD='secret' python3 script.py
```

Prefer:

```bash
cp .env.example .env
$EDITOR .env
python3 script.py
```

or a headed login:

```bash
python3 script.py --login --headed
```

