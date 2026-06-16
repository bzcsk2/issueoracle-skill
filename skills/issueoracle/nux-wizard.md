# IssueOracle - First Run Wizard

Welcome to IssueOracle! This guide helps you get started.

## Step 1: Verify Installation

```bash
# Check that everything works
cd issueoracle-skill
python3 skills/issueoracle/scripts/issueoracle.py diagnose
```

You should see environment information including Python version, pack status, and GitHub API quota.

## Step 2: (Optional) Configure GitHub Token

For higher API rate limits (5000/hr instead of 60/hr):

```bash
# Set environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Or create config file
mkdir -p ~/.issueoracle
cat > ~/.issueoracle/config.toml << 'EOF'
github_token = "ghp_your_token_here"
severity_threshold = "medium"
EOF
```

## Step 3: Review Local Code

```bash
# Review current directory
/issueoracle review .

# Review with JSON output
/issueoracle review . --emit json

# Review only changed files
/issueoracle review . --changed --base main
```

## Step 4: Mine Bug Patterns

```bash
# Mine from a GitHub repo
/issueoracle mine fastapi/fastapi --max-issues 10

# Results saved to ~/.issueoracle/mining/
# Review candidates in the review.md file
```

## Step 5: Understand Output

Each finding includes:
- File and line numbers
- Confidence score (0.0 - 1.0)
- Matched pattern ID
- Trigger condition
- Local evidence
- OSS evidence link
- Suggested fix
- False-positive boundary
