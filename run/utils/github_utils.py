import os
import sys

try:
    from google.cloud import secretmanager
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False

def get_github_token():
    """Retrieve GitHub token from env or Google Secret Manager (GCP)"""
    import sys

    # Try environment variable (local dev)
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        print("[DEBUG] GitHub token loaded from environment variable", file=sys.stderr)
        return token

    # Fallback to Google Cloud Secret Manager
    if CLOUD_AVAILABLE:
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                print("[ERROR] GOOGLE_CLOUD_PROJECT not set in environment", file=sys.stderr)
                return None

            name = f"projects/{project_id}/secrets/github-token/versions/latest"
            response = client.access_secret_version(request={"name": name})
            token = response.payload.data.decode("UTF-8")

            print(f"[DEBUG] GitHub token retrieved from Secret Manager. Length: {len(token)}", file=sys.stderr)
            return token

        except Exception as e:
            print(f"[ERROR] Failed to retrieve GitHub token from Secret Manager: {e}", file=sys.stderr)
            return None

    print("[ERROR] GitHub token not found: no environment variable and no GCP access", file=sys.stderr)
    return None
