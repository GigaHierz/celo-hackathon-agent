#!/bin/bash

# Mento Analysis Runner Script
# This script demonstrates how to run analysis using the mento.txt prompt

echo "🔍 Running Mento Protocol Analysis..."
echo "📁 Reports will be saved to: mento-reports-pos/"
echo "📋 Using prompt: config/prompts/mento.txt"
echo ""

# Example command structure (replace with actual repository URLs)
echo "Example command:"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/user/repo1,https://github.com/user/repo2\" \\"
echo "  --prompt \"config/prompts/mento.txt\" \\"
echo "  --output \"mento-reports-pos\" \\"
echo "  --model \"gemini-2.5-flash\""
echo ""

# Since the defaults are now set, you can simply run:
echo "Simplified command (uses mento.txt and mento-reports-pos by default):"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/user/repo1,https://github.com/user/repo2\""
echo ""

echo "🎯 For a quick test with a real repository:"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/mento-protocol/mento-sdk\""
echo ""

echo "✅ The system will now:"
echo "   1. Analyze repositories using Mento-focused prompts"
echo "   2. Generate individual analysis reports in mento-reports-pos/"
echo "   3. Create/update mento-summary.md with aggregated results"
echo "   4. Score projects based on Mento Protocol integration quality"
echo ""

echo "🚀 Ready to analyze! Run one of the commands above with your repository URLs."
