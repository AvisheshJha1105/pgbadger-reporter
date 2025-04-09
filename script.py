import os
import sys
import subprocess
import boto3
import multiprocessing
from datetime import datetime, timedelta, timezone
import pdfkit

region = os.getenv("AWS_DEFAULT_REGION", "us-east-1").strip()

rds_client = boto3.client("rds", region_name=region)
s3_client = boto3.client("s3", region_name=region)

DB_INSTANCE = "aurora-pg-instance-1"
DOWNLOAD_DIR = "/tmp/rds_downloaded_logs/error"
REPORT_DIR = "/tmp/rds_downloaded_logs/report"
PDF_REPORT_DIR = "/tmp/rds_downloaded_logs/pdf_report"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(PDF_REPORT_DIR, exist_ok=True)

def install_pgBadger():
    try:
        subprocess.check_call(["pgbadger", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ pgBadger is already installed.")
    except subprocess.CalledProcessError:
        print("📦 Installing pgBadger...")
        subprocess.check_call(["apt-get", "install", "-y", "pgbadger"])

def get_time_range(choice: str):
    now = datetime.now(timezone.utc)
    if choice == "1":
        return now - timedelta(hours=24), now
    elif choice == "2":
        return now - timedelta(hours=48), now
    elif choice == "3":
        return now - timedelta(days=7), now
    else:
        print("❌ Invalid time range choice. Use 1 (24h), 2 (48h), or 3 (7 days).")
        sys.exit(1)

def get_logs_in_time_range(start, end):
    print(f"🔍 Fetching logs between {start} and {end} UTC...")
    try:
        logs = rds_client.describe_db_log_files(DBInstanceIdentifier=DB_INSTANCE)["DescribeDBLogFiles"]
        return [
            log["LogFileName"]
            for log in logs
            if start <= datetime.fromtimestamp(log["LastWritten"] / 1000, timezone.utc) <= end
        ]
    except Exception as e:
        print(f"❌ Error fetching log files: {e}")
        sys.exit(1)

def download_and_generate_report(log_file_name):
    log_path = os.path.join(DOWNLOAD_DIR, os.path.basename(log_file_name))
    try:
        print(f"⏬ Downloading {log_file_name}...")
        with open(log_path, "wb") as f:
            marker = '0'
            while marker:
                response = rds_client.download_db_log_file_portion(
                    DBInstanceIdentifier=DB_INSTANCE,
                    LogFileName=log_file_name,
                    Marker=marker
                )
                log_data = response.get("LogFileData", "")
                marker = response.get("Marker", "")
                if not log_data:
                    break
                f.write(log_data.encode())
        print(f"✅ Saved: {log_path}")
        generate_pgbadger_report(log_path)
    except Exception as e:
        print(f"❌ Error downloading {log_file_name}: {e}")

def generate_pgbadger_report(log_file_path):
    report_file = os.path.join(REPORT_DIR, os.path.basename(log_file_path) + ".html")
    try:
        print(f"🛠 Generating report for {log_file_path}...")
        subprocess.check_call(["pgbadger", log_file_path, "-o", report_file])
        print(f"📄 Report saved: {report_file}")
        convert_html_to_pdf(report_file)
    except subprocess.CalledProcessError as e:
        print(f"❌ pgBadger failed for {log_file_path}: {e}")

def convert_html_to_pdf(html_file_path):
    try:
        pdf_file = os.path.join(PDF_REPORT_DIR, os.path.basename(html_file_path) + ".pdf")
        print(f"🖨 Converting {html_file_path} to PDF...")
        pdfkit.from_file(html_file_path, pdf_file)
        print(f"✅ PDF report saved: {pdf_file}")
    except Exception as e:
        print(f"❌ Error converting {html_file_path} to PDF: {e}")

def upload_reports_to_s3(bucket_name, report_dir):
    if not bucket_name:
        raise ValueError("❌ S3 bucket name is empty.")
    try:
        for filename in os.listdir(report_dir):
            if filename.endswith(".html") or filename.endswith(".pdf"):
                file_path = os.path.join(report_dir, filename)
                s3_client.upload_file(file_path, bucket_name, filename)
                print(f"⬆ Uploaded {filename} to S3 bucket {bucket_name}.")
    except Exception as e:
        print(f"❌ Error uploading reports to S3: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <s3_bucket_name> <time_range>")
        print("  time_range: 1 (24h), 2 (48h), 3 (7d)")
        sys.exit(1)

    bucket_name = sys.argv[1].strip()
    time_range_choice = sys.argv[2].strip()

    install_pgBadger()
    start_timestamp, end_timestamp = get_time_range(time_range_choice)
    log_filenames = get_logs_in_time_range(start_timestamp, end_timestamp)

    if not log_filenames:
        print("⚠ No logs found for the selected time range.")
        return

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(download_and_generate_report, log_filenames)

    print(f"✅ All reports saved in {REPORT_DIR}")
    upload_reports_to_s3(bucket_name, REPORT_DIR)
    upload_reports_to_s3(bucket_name, PDF_REPORT_DIR)
    print(f"🎉 Reports uploaded to S3 bucket: {bucket_name}")

if __name__ == "__main__":
    main()
