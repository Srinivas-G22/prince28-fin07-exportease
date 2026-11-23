from botocore.exceptions import ClientError

from scripts.upload_raw import ensure_bucket, upload_raw


class RecordingS3:
    def __init__(self, bucket_exists: bool = True) -> None:
        self.bucket_exists = bucket_exists
        self.checked: list[str] = []
        self.created: list[str] = []
        self.uploads: list[tuple[str, str, str]] = []

    def head_bucket(self, *, Bucket: str) -> object:
        self.checked.append(Bucket)
        if not self.bucket_exists:
            raise ClientError(
                {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadBucket",
            )
        return {}

    def create_bucket(self, *, Bucket: str) -> object:
        self.created.append(Bucket)
        return {}

    def upload_file(self, Filename: str, Bucket: str, Key: str) -> None:
        self.uploads.append((Filename, Bucket, Key))


def test_ensure_bucket_creates_missing_bucket():
    client = RecordingS3(bucket_exists=False)

    ensure_bucket(client, "exportease-raw")

    assert client.created == ["exportease-raw"]


def test_upload_preserves_raw_paths_and_skips_git_metadata_and_partial_files(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    source = raw_dir / "dgft" / "policy.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"%PDF-")
    (raw_dir / "repo" / ".git").mkdir(parents=True)
    (raw_dir / "repo" / ".git" / "config").write_text("metadata")
    (raw_dir / "dgft" / "unfinished.part").write_text("partial")
    client = RecordingS3()

    uploaded = upload_raw(client, "exportease-raw", tmp_path)

    assert uploaded == 1
    assert client.uploads == [(str(source), "exportease-raw", "data/raw/dgft/policy.pdf")]
