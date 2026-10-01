# MinIO Environment Optimizations

These settings are specifically for resource-constrained environments (e.g., Oracle Free Tier) to minimize CPU and RAM overhead.

## 🛠️ Recommended Environment Variables

| Variable | Value | Description |
| :--- | :--- | :--- |
| `MINIO_BROWSER` | `off` | Disables the web console UI, saving significant RAM. |
| `MINIO_CI_CD` | `true` | Enables lightweight mode, reducing base memory allocation. |
| `MINIO_STORAGE_CLASS_STANDARD` | `EC:0` | Disables Erasure Coding. Essential for single-node setups to save CPU/RAM. |
| `MINIO_STORAGE_CLASS_RRS` | `EC:0` | Disables EC for Reduced Redundancy Storage. |
| `MINIO_API_REQUESTS_MAX` | `100` | Limits maximum concurrent API requests. |
| `MINIO_API_REQUESTS_MAX_PER_NODE` | `50` | Limits requests per node. |

## 📉 Resource Targets (Dokploy/Docker)
- **Memory Limit**: `128M` (can be lowered to `96M` if monitoring shows low usage).
- **CPU Limit**: `0.25` (25% of a core).
