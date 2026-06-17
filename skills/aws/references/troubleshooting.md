# AWS CLI Troubleshooting

A decision tree for the errors that actually show up. Start with `aws sts get-caller-identity` — it answers "right identity? right account?" in one shot.

## Docs
- Troubleshooting the CLI: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-troubleshooting.html
- Config/credential resolution: https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html
- Request throttling & retries: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-retries.html

---

## First move, always

```bash
aws sts get-caller-identity            # Account + Arn you're actually using
aws configure list                     # which profile/region/source resolved
echo "$AWS_PROFILE $AWS_REGION $AWS_ACCESS_KEY_ID"   # env shadowing check
```

If the `Arn`/`Account` is not what you expect, it's a profile/credential problem — fix that before touching IAM policies.

---

## AccessDenied / not authorized to perform

The identity is valid but lacks permission, **or** you're in the wrong account.

```bash
# 1. Confirm identity & account
aws sts get-caller-identity

# 2. The error message names the exact action + resource — read it:
#    "User: arn:...:user/alice is not authorized to perform: s3:GetObject on resource: ..."

# 3. Check the policies attached to that principal
aws iam list-attached-user-policies --user-name alice
aws iam list-attached-role-policies --role-name MyRole
```

Common real causes: wrong account/profile, missing action in the policy, a resource-level restriction (bucket policy / KMS key policy), or an SCP/permission boundary. Region-scoped resource ARNs in the policy that don't match `--region` also bite.

---

## ExpiredToken / The security token included in the request is expired

Temporary credentials (SSO or assumed-role) timed out.

```bash
aws sso login --profile dev            # SSO: re-authenticate
# Assumed-role/manual STS creds: re-run assume-role and re-export the env vars
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN   # clear stale env
```

This is almost never a permissions issue — do not start editing IAM policies.

---

## You must specify a region / region not set

No region resolved from any source.

```bash
aws s3 ls --region us-east-1                    # one-off
export AWS_REGION=us-east-1                      # this shell
aws configure set region us-east-1 --profile X  # persist to profile
```

Resolution order for region: `--region` flag → `AWS_REGION` → `AWS_DEFAULT_REGION` → profile's `region` in `~/.aws/config`. S3/IAM partial-exception aside, most services hard-fail without one.

---

## Throttling / Rate exceeded / ThrottlingException

You're hitting API rate limits. The CLI retries with backoff, but tune it:

```bash
export AWS_RETRY_MODE=adaptive     # standard | adaptive
export AWS_MAX_ATTEMPTS=10
# or per-profile in ~/.aws/config:  retry_mode = adaptive / max_attempts = 10
```

Also reduce request volume: use server-side `--filters`/`--query`, larger `--page-size`, and avoid tight loops over `describe-*`.

---

## Wrong account / profile being used (silent)

```bash
# Trace precedence: flag > env > credentials file > config file > SSO/role cache > IMDS
aws configure list                 # Value + Type column shows the source
env | grep -i aws                  # env vars silently override files
```

An exported `AWS_PROFILE` or stray `AWS_ACCESS_KEY_ID` is the usual culprit — it shadows the `--profile` you *think* you're using only if no `--profile` flag is passed (flags still win).

---

## `--debug` — the nuclear option

Dumps the full credential-provider chain, the signed request, headers, and the raw response. Best single tool for "why did it pick that identity/region/endpoint".

```bash
aws s3 ls --debug 2>&1 | grep -iE "credential|profile|region|endpoint"
aws s3 ls --debug 2>&1 | grep -i "Found credentials"   # which provider won
```

---

## SSL / endpoint / connectivity

```bash
# Corporate proxy / custom CA
export HTTPS_PROXY=http://proxy:8080
export AWS_CA_BUNDLE=/path/to/ca.pem
aws s3 ls --no-verify-ssl              # last resort, debugging only — do NOT leave on

# Test against an alternate endpoint (LocalStack, VPC endpoint, GovCloud)
aws s3 ls --endpoint-url http://localhost:4566
```

---

## Quick reference table

| Symptom | Likely cause | Fix |
|---|---|---|
| `Unable to locate credentials` | no profile/env/IMDS creds | set `--profile`/env, or `aws sso login` |
| `ExpiredToken` | SSO/STS session timed out | re-login / re-assume role |
| `AccessDenied` | missing perm or wrong account | check `get-caller-identity` + policies |
| `You must specify a region` | no region resolved | `--region` / `AWS_REGION` / config |
| `ThrottlingException` | rate limit | `AWS_RETRY_MODE=adaptive`, fewer calls |
| wrong account silently | env var shadowing | `env | grep aws`; `aws configure list` |
