# Core AWS Services — CLI Cheat-Sheet

The day-to-day operations for the five services you touch most. All commands respect `--profile` / `--region`.

## Docs
- S3 (`aws s3` / `s3api`): https://docs.aws.amazon.com/cli/latest/reference/s3/index.html
- EC2: https://docs.aws.amazon.com/cli/latest/reference/ec2/index.html
- IAM: https://docs.aws.amazon.com/cli/latest/reference/iam/index.html
- Lambda: https://docs.aws.amazon.com/cli/latest/reference/lambda/index.html
- CloudWatch Logs: https://docs.aws.amazon.com/cli/latest/reference/logs/index.html

---

## S3

`aws s3` = high-level (cp/sync/ls). `aws s3api` = low-level 1:1 API access.

```bash
# List buckets / objects
aws s3 ls
aws s3 ls s3://my-bucket/path/ --recursive --human-readable --summarize

# Copy / move / remove
aws s3 cp ./file.txt s3://my-bucket/path/
aws s3 cp s3://my-bucket/path/file.txt ./        # download
aws s3 mv s3://my-bucket/a.txt s3://my-bucket/b.txt
aws s3 rm s3://my-bucket/path/ --recursive

# Sync a directory (--delete removes extras on the destination)
aws s3 sync ./dist s3://my-bucket/ --delete --exclude "*.map"

# Presigned URL (temporary public download link)
aws s3 presign s3://my-bucket/file.txt --expires-in 3600

# s3api for fine control
aws s3api create-bucket --bucket my-bucket \
  --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
aws s3api put-object --bucket my-bucket --key k --body ./file.txt
aws s3api head-object --bucket my-bucket --key k    # metadata / existence check
```

Note: `create-bucket` outside `us-east-1` **requires** `LocationConstraint`; in `us-east-1` you must omit it.

---

## EC2

```bash
# Describe (use --filters to query server-side)
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`]|[0].Value]' \
  --output table

# Lifecycle
aws ec2 start-instances  --instance-ids i-0abc123
aws ec2 stop-instances   --instance-ids i-0abc123
aws ec2 reboot-instances --instance-ids i-0abc123
aws ec2 terminate-instances --instance-ids i-0abc123

# Launch
aws ec2 run-instances --image-id ami-012345 --instance-type t3.micro \
  --key-name my-key --security-group-ids sg-0abc --subnet-id subnet-0abc --count 1

# Networking / keys / images
aws ec2 describe-security-groups --query 'SecurityGroups[].[GroupId,GroupName]' --output table
aws ec2 describe-images --owners self --query 'Images[].[ImageId,Name]' --output table
aws ec2 create-key-pair --key-name my-key --query 'KeyMaterial' --output text > my-key.pem
```

---

## IAM

```bash
# Who / what exists
aws iam get-user
aws iam list-users  --query 'Users[].UserName' --output text
aws iam list-roles  --query 'Roles[].RoleName' --output text
aws iam list-attached-role-policies --role-name MyRole

# Inspect a policy document
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam get-policy-version --policy-arn <arn> --version-id v1

# Access keys
aws iam list-access-keys --user-name alice
aws iam create-access-key --user-name alice
aws iam delete-access-key --user-name alice --access-key-id AKIA...

# Create a role with a trust policy
aws iam create-role --role-name MyRole \
  --assume-role-policy-document file://trust.json
aws iam attach-role-policy --role-name MyRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

IAM is **global** (region-agnostic) but the CLI still routes through `us-east-1`; a wrong region rarely breaks IAM but a wrong account/profile will.

---

## Lambda

```bash
# List / inspect
aws lambda list-functions --query 'Functions[].FunctionName' --output text
aws lambda get-function --function-name my-fn
aws lambda get-function-configuration --function-name my-fn

# Invoke (v2 requires --cli-binary-format for raw JSON payloads)
aws lambda invoke --function-name my-fn \
  --cli-binary-format raw-in-base64-out \
  --payload '{"key":"value"}' /tmp/out.json
cat /tmp/out.json

# Deploy code
aws lambda update-function-code --function-name my-fn --zip-file fileb://fn.zip
aws lambda update-function-configuration --function-name my-fn \
  --environment "Variables={LOG_LEVEL=debug}" --timeout 30 --memory-size 256
```

---

## CloudWatch Logs

```bash
# Tail in real time (the fastest way to watch a Lambda/app)
aws logs tail /aws/lambda/my-fn --follow
aws logs tail /aws/lambda/my-fn --since 1h --format short

# Discover log groups / streams
aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text
aws logs describe-log-streams --log-group-name /aws/lambda/my-fn \
  --order-by LastEventTime --descending --max-items 5

# Filter across all streams in a group
aws logs filter-log-events --log-group-name /aws/lambda/my-fn \
  --filter-pattern "ERROR" --start-time $(($(date +%s)*1000 - 3600000))

# Logs Insights query
qid=$(aws logs start-query --log-group-name /aws/lambda/my-fn \
  --start-time $(($(date +%s) - 3600)) --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | sort @timestamp desc | limit 20' \
  --query queryId --output text)
aws logs get-query-results --query-id "$qid"
```
