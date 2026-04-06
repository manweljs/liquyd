# config.py
import os

from dotenv import load_dotenv

load_dotenv()


LIQUYD_CONFIG = {
    "default": {
        "engine": "opensearch",
        "hosts": [
            {
                "host": os.getenv("OPENSEARCH_HOST", "localhost"),
                "port": int(os.getenv("OPENSEARCH_PORT", "9200")),
            }
        ],
        "http_auth": (
            os.getenv("OPENSEARCH_USERNAME", "admin"),
            os.getenv("OPENSEARCH_PASSWORD", ""),
        ),
        "use_ssl": os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true",
        "verify_certs": os.getenv("OPENSEARCH_VERIFY_SSL", "true").lower() == "true",
    }
}
