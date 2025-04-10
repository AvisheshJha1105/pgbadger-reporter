# pgbadger-reporter
pgbadger-reporter is a Dockerized tool that automates the download of RDS logs, generates pgBadger reports for the past 24 hours, 48 hours, and one week, and uploads the reports to an S3 bucket.

🚀 pgBadger Reporter – Setup & Usage Guide
✅ 1. Set Up AWS Credentials
Make sure your system has the following files:

🗂 ~/.aws/credentials

[default]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
aws_session_token=YOUR_SESSION_TOKEN  # (optional for long-lived keys)
🗂 ~/.aws/config

[default]
region=us-east-1
output=json
🔒 Secure your credential files:

chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config
🧩 2. Clone the Repository
bash
Copy
Edit
git clone https://github.com/avisheshjha1105/pgbadger-reporter.git
cd pgbadger-reporter
🛠️ 3. Build the Docker Image
bash

docker build -t pgbadger-reporter .
🐳 4. Run the Docker Container
bash

docker run --rm \
  -v ~/.aws:/root/.aws \
  -e AWS_PROFILE=default \
  pgbadger-reporter your-s3-bucket-name 1
Replace:

your-s3-bucket-name → the name of your S3 bucket

1 → time range:
1 = Last 24 hours
2 = Last 48 hours
3 = Last 7 days

✅ What Happens When You Run It
📥 Downloads PostgreSQL logs from AWS RDS

📊 Analyzes logs using pgBadger

🖨 Converts reports from HTML to PDF

☁ Uploads both formats to your S3 bucket


