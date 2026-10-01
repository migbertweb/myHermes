---
name: alibaba-cloud-dashscope-setup
version: 1.0.0
description: Configure, diagnose, and troubleshoot Alibaba Cloud DashScope as a model provider in Hermes Agent
author: Hermes Agent
tags: [alibaba, dashscope, qwen, deepseek, model-provider, token-management]
---

# Alibaba Cloud DashScope Setup

This skill provides guidance for configuring, managing, and troubleshooting Alibaba Cloud DashScope as a model provider in Hermes Agent.

## Setup Instructions

### 1. Obtain API Key
- Register for an Alibaba Cloud account at https://www.alibabacloud.com/
- Navigate to the DashScope console: https://dashscope.console.aliyun.com/
- Create or retrieve your API key from the API Key Management section

### 2. Configure in Hermes
Add the following to your Hermes configuration (`~/.hermes/config.yaml`):

```yaml
providers:
  alibaba:
    type: openai-compatible
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: YOUR_API_KEY_HERE
```

### 3. Available Models
DashScope provides access to various models including:
- Qwen series (Qwen-Max, Qwen-Plus, Qwen-Turbo)
- DeepSeek models (DeepSeek-V4-Flash, DeepSeek-V4-Pro)
- Other third-party models

## Free Tier Information

### Token Allowance
- New users typically receive **70+ million free tokens** for Model Studio/DashScope
- Free tokens apply to most models including DeepSeek-V4-Flash

### Validity Period
- Free credits for new users are typically valid for **90 days**
- This follows Alibaba Cloud's standard free trial policy
- **Important**: Always verify the exact expiration date in your DashScope console

### Usage Optimization
- **DeepSeek-V4-Flash** is more token-efficient than DeepSeek-V4-Pro
- For intermediate usage (~10,000-12,000 tokens/day), free credits should last the full 90-day period
- Monitor usage in the DashScope console to avoid unexpected charges

## Troubleshooting

### Common Issues
1. **Authentication errors**: Verify your API key is correctly configured
2. **Model not found**: Ensure you're using the correct model name as listed in DashScope
3. **Rate limiting**: Free tier may have rate limits; consider upgrading for production use

### Verification Steps
1. Check your API key in the DashScope console
2. Verify model availability in the Model Studio section
3. Monitor token consumption in the billing dashboard

## References
- [Alibaba Cloud Free Trial](https://www.alibabacloud.com/es/free)
- [DashScope Documentation](https://help.aliyun.com/zh/dashscope/)
- See `references/token-efficiency.md` for detailed token usage estimates and model efficiency comparisons