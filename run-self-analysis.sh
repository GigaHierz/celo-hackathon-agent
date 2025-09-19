#!/bin/bash

# Self Analysis Runner Script
# This script demonstrates how to run analysis using the self.txt prompt

echo "🔍 Running Self Protocol Analysis..."
echo "📁 Reports will be saved to: self-reports-pos/"
echo "📋 Using prompt: config/prompts/self.txt"
echo ""

# Example command structure (replace with actual repository URLs)
echo "Example command:"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/user/repo1,https://github.com/user/repo2\" \\"
echo "  --prompt \"config/prompts/self.txt\" \\"
echo "  --output \"self-reports-pos\" \\"
echo "  --model \"gemini-2.5-flash\""
echo ""

# Since the defaults are now set, you can simply run:
echo "Simplified command (uses self.txt and self-reports-pos by default):"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/user/repo1,https://github.com/user/repo2\""
echo ""

echo "🎯 For a quick test with a real repository:"
echo "uv run python packages/cli/src/main.py \\"
echo "  --github-urls \"https://github.com/self-protocol/self-sdk\""
echo ""

echo "✅ The system will now:"
echo "   1. Analyze repositories using self-focused prompts"
echo "   2. Generate individual analysis reports in self-reports-pos/"
echo "   3. Create/update self-summary.md with aggregated results"
echo "   4. Score projects based on self Protocol integration quality"
echo ""

echo "🚀 Ready to analyze! Run one of the commands above with your repository URLs."
