"""Create the configured Cloudflare R2 bucket and upload data/raw/ with its path prefix."""

import os
from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

DEFAULT_BUCKET = "exportease-raw"


class S3Client(Protocol):
    def head_bucket(self, *, Bucket: str) -> object: ...

    def create_bucket(self, *, Bucket: str) -> object: ...

    def upload_file(self, Filename: str, Bucket: str, Key: str) -> None: ...


def ensure_bucket(client: S3Client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as error:
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = error.response.get("Error", {}).get("Code")
        if status != 404 and code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)


def upload_raw(client: S3Client, bucket: str, project_root: Path | None = None) -> int:
    project_root = (project_root or Path.cwd()).resolve()
    raw_dir = project_root / "data" / "raw"
    if not raw_dir.is_dir():
        raise FileNotFoundError(raw_dir)
    files = sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(raw_dir).parts
        and not path.name.endswith(".part")
    )
    for path in files:
        client.upload_file(
            Filename=str(path),
            Bucket=bucket,
            Key=path.relative_to(project_root).as_posix(),
        )
    return len(files)


def main() -> int:
    load_dotenv()
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit(f"Set {', '.join(missing)} in .env before uploading.")

    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.getenv("R2_BUCKET") or DEFAULT_BUCKET
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    ensure_bucket(client, bucket)
    count = upload_raw(client, bucket)
    print(f"bucket={bucket} uploaded={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
