# AWS Authentication & Credentials

How the CLI/SDK decides *who* you are and *which account* you hit. Most "weird AWS" bugs are auth-resolution bugs.

## Docs
- Credentials config & files: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
- Credential provider chain: https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html
- Assume an IAM role: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html
- SSO config: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html
- Env vars: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html

---

## Resolution order (first match wins)

1. **Command-line flags** — `--profile`, `--region` (and per-request `--endpoint-url`)
2. **Environment variables** — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`, `AWS_REGION`
3. **`~/.aws/credentials`** — static keys keyed by profile
4. **`~/.aws/config`** — profile settings, `role_arn` + `source_profile`, `sso_*`, `credential_process`
5. **SSO / assumed-role cache** — `~/.aws/sso/cache`, `~/.aws/cli/cache`
6. **Container credentials** — `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` (ECS/Fargate)
7. **EC2 instance profile** — IMDS at `169.254.169.254`

```bash
# See exactly what got resolved and the source of each value
aws configure list
aws sts get-caller-identity     # the ground truth: Account, UserId, Arn
```

---

## File format

`~/.aws/credentials` (secrets only):

```ini
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = wJalr...

[ci]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

`~/.aws/config` (settings; profiles need a `profile ` prefix here, except `default`):

```ini
[default]
region = us-east-1
output = json

[profile prod]
region = us-west-2
output = table
```

Never commit either file. If `aws_access_key_id` shows up in git, rotate it immediately.

---

## Environment variables

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...        # required for temporary (STS) creds
export AWS_PROFILE=prod             # pick a profile without --profile
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2 # fallback if AWS_REGION unset
```

Env vars override the config files but are overridden by explicit `--profile`/`--region` flags.

---

## Assume an IAM role (cross-account / privilege change)

Config-file way — CLI assumes the role automatically on every call:

```ini
[profile target]
role_arn = arn:aws:iam::222222222222:role/DeployRole
source_profile = default          # creds used to call sts:AssumeRole
region = us-east-1
# mfa_serial = arn:aws:iam::111111111111:mfa/alice   # prompt for MFA if required
```

```bash
aws s3 ls --profile target        # transparently assumes DeployRole
```

Manual way — get temporary creds yourself:

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::222222222222:role/DeployRole \
  --role-session-name my-session \
  --query 'Credentials' --output json

# Export them
creds=$(aws sts assume-role --role-arn arn:aws:iam::222:role/DeployRole \
  --role-session-name s --query Credentials --output text)
export AWS_ACCESS_KEY_ID=$(echo "$creds" | cut -f1)
export AWS_SECRET_ACCESS_KEY=$(echo "$creds" | cut -f3)
export AWS_SESSION_TOKEN=$(echo "$creds" | cut -f4)
```

---

## MFA

```bash
# Get a 1-hour session token gated by an MFA code
aws sts get-session-token \
  --serial-number arn:aws:iam::111111111111:mfa/alice \
  --token-code 123456 \
  --duration-seconds 3600
```

For role assumption, put `mfa_serial` in the profile (above) and the CLI prompts for the code.

---

## SSO (IAM Identity Center)

```ini
[profile dev]
sso_session = my-org
sso_account_id = 111111111111
sso_role_name = PowerUserAccess
region = us-east-1

[sso-session my-org]
sso_start_url = https://my-org.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

```bash
aws configure sso --profile dev    # initial setup (writes the above)
aws sso login --profile dev        # browser auth; caches a short-lived token
aws sts get-caller-identity --profile dev
```

SSO sessions expire — `ExpiredToken` here means re-run `aws sso login`, not a policy fix.

---

## EC2 instance profiles & container roles

On EC2/ECS, attach a role instead of shipping keys. The CLI auto-discovers them via the metadata service — no keys, no profile needed.

```bash
# On the instance: confirm the role and inspect creds source
aws sts get-caller-identity
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/   # IMDSv1
# IMDSv2 (token-required):
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

If a local profile/env var is set, it **shadows** the instance profile — unset them to fall through to the role.
