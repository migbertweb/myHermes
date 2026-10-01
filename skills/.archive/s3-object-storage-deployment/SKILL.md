---
name: s3-object-storage-deployment
description: Procedures for deploying and optimizing S3-compatible object storage (MinIO, Garage, SeaweedFS) on resource-constrained environments like Oracle Free Tier.
tags: [s3, object-storage, minio, garage, seaweedfs, optimization, oracle-free-tier]
---

# S3 Object Storage Deployment

This skill governs the selection, deployment, and resource optimization of S3-compatible object storage, specifically for small VPS or "Free Tier" environments where RAM and CPU are the primary bottlenecks.

## 🚀 Selection Guide

Choose based on available resources and requirements:

| Solution | RAM (Idle/Low) | Best For | Tech Stack | License |
| :--- | :--- | :--- | :--- | :--- |
| **MinIO** | ~256MB+ (Optimized) | High S3 API parity, Enterprise features | Go | AGPLv3 |
| **Garage** | ~50-100MB | Very light, Geo-distribution, Rust efficiency | Rust | AGPLv3 |
| **SeaweedFS** | ~30-80MB | High I/O, Modular scaling, "Mini" mode | Go | Apache 2.0 |
| **RustFS** | ~80-150MB | Max performance on small objects | Rust | Mixed |

## 🛠️ Optimization Patterns

### MinIO Low-Resource Mode
By default, MinIO can be RAM-hungry. Use these flags to prevent OOM kills on 1GB RAM servers:

1. **Force Low Memory**: Set `MINIO_CI_CD=true`. This reduces the internal memory allocation from ~2GB to ~256MB.
2. **Disable UI**: Set `MINIO_BROWSER=off` to kill the console process and save ~200MB RAM.
3. **Resource Limits**: Always set Docker memory limits (e.g., `memory: 256M`) to prevent the container from spiking and crashing the host.

### Garage Deployment
Designed for lightweight self-hosting.
- **Config**: Uses TOML.
- **Persistence**: Ensure `/var/lib/garage` is mapped to a durable volume.
- **Resource Target**: Can comfortably run under 128MB RAM.

### SeaweedFS "Mini" Mode
For single-node setups, use the "mini" or combined server mode to avoid running separate master/volume/s3 processes.
- **Command**: `weed server -s3` or `weed mini`.

## ⚠️ Pitfalls & Lessons

- **OOM Killers**: On Oracle Free Tier (AMD/ARM), the OS will kill the process without warning if RAM spikes. Always use `MINIO_CI_CD=true` for MinIO.
- **S3 API Parity**: Garage is lightweight but may lack some advanced S3 features compared to MinIO (e.g., complex lifecycle rules).
- **Single-Node Optimization**: For MinIO on single-node setups, always disable Erasure Coding (`EC:0`) to avoid unnecessary CPU overhead.
- **Storage Performance**: SeaweedFS generally outperforms others for massive amounts of small files due to its index architecture.

## 📖 References
- See `references/minio-optimizations.md` for a detailed list of env vars for MinIO.
- See `templates/docker-compose-s3.yaml` for a multi-variant starter.
