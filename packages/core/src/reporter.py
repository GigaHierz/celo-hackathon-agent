"""
Reporter module for the AI Project Analyzer.

This module handles saving analysis reports to files in various formats.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)

# Supported report formats
REPORT_FORMATS = ["md", "json", "html", "csv"]


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure that the directory exists, create it if it doesn't.

    Args:
        directory: Directory path to check/create
    """
    os.makedirs(directory, exist_ok=True)
    logger.debug(f"Ensured directory exists: {directory}")


def generate_report_directory(base_output_dir: str) -> str:
    """
    Generate a timestamped directory for reports.

    Args:
        base_output_dir: Base directory for reports

    Returns:
        str: Path to the timestamped directory
    """
    # Create timestamp-based directory
    timestamp = datetime.now().strftime("%m-%d-%Y-%H%M")
    report_dir = os.path.join(base_output_dir, timestamp)

    # Ensure the directory exists
    ensure_directory_exists(report_dir)

    return report_dir


def generate_filename(repo_name: str) -> str:
    """
    Generate a filename for the report.

    Args:
        repo_name: Name of the repository

    Returns:
        str: Generated filename
    """
    # Replace slashes with hyphens for file safety
    safe_name = repo_name.replace("/", "-")

    return f"{safe_name}-analysis.md"


def save_report(repo_name: str, analysis, output_dir: str) -> str:
    """
    Save an individual analysis report to a file.

    Args:
        repo_name: Name of the repository
        analysis: Analysis report content (string or dictionary)
        output_dir: Directory to save the report

    Returns:
        str: Path to the saved report file
    """
    # Ensure the output directory exists
    ensure_directory_exists(output_dir)

    # Determine if we're dealing with JSON or Markdown
    is_json = isinstance(analysis, dict)

    # Generate filename with appropriate extension
    file_ext = "json" if is_json else "md"
    base_filename = generate_filename(repo_name)
    filename = f"{os.path.splitext(base_filename)[0]}.{file_ext}"

    # Full path to the report file
    report_path = os.path.join(output_dir, filename)

    # Save the report based on its type
    if is_json:
        # Add metadata to JSON
        analysis_with_metadata = {
            "repository": repo_name,
            "generated_at": datetime.now().isoformat(),
            "analysis": analysis,
        }

        # Save as JSON
        with open(report_path, "w", encoding="utf-8") as f:
            import json

            json.dump(analysis_with_metadata, f, indent=2)
    else:
        # For markdown, add header with repository name and timestamp
        header = f"# Analysis Report: {repo_name}\n\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Handle error messages specially
        if isinstance(analysis, str) and analysis.startswith("Error:"):
            header += f"\n## Error\n\n{analysis}\n"
            content = header
        else:
            content = header + analysis

        # Save as Markdown
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

    return report_path


def extract_mento_scores_from_markdown(markdown_content: str) -> Dict[str, float]:
    """
    Extract Mento-specific scores from markdown analysis content.

    Args:
        markdown_content: Markdown-formatted analysis text

    Returns:
        Dict[str, float]: Dictionary of extracted Mento scores (0-10 scale with decimals)
    """
    scores = {}

    # For debugging
    logger.debug(f"Extracting Mento scores from markdown content of length: {len(markdown_content)}")

    # Check for the special case where content is wrapped in ```markdown blocks
    if markdown_content.startswith("```markdown") or markdown_content.startswith("```"):
        logger.debug(
            "Content appears to be wrapped in markdown code blocks, extracting inner content"
        )
        lines = markdown_content.splitlines()
        # Find the first and last code block markers
        start_idx = next((i for i, line in enumerate(lines) if line.startswith("```")), 0)
        end_idx = (
            len(lines) - 1 - next((i for i, line in enumerate(reversed(lines)) if line == "```"), 0)
        )

        # Extract the content between the markers (if they exist)
        if start_idx < end_idx:
            # Skip the first line with ```markdown
            inner_content = "\n".join(lines[start_idx + 1 : end_idx])
            if inner_content:
                logger.debug(f"Extracted inner markdown content of length: {len(inner_content)}")
                markdown_content = inner_content

    # First try to extract from the score table (preferred method)
    # Pattern looks for a number that can be an integer or decimal followed by /10 (e.g., 8/10 or 8.5/10)
    table_pattern = r"\|\s*([^|]+)\s*\|\s*(\d+(?:\.\d+)?)(?:/10)?\s*\|"
    table_matches = re.findall(table_pattern, markdown_content)
    logger.debug(f"Found {len(table_matches)} potential score matches in table format")

    if table_matches:
        for criterion, score_str in table_matches:
            criterion = criterion.strip().lower()
            try:
                # Remove "/10" if present in the score string
                score_str = score_str.strip().replace("/10", "").strip()
                score = float(score_str)

                # Log what we found
                logger.debug(f"Found score: {score} for criterion: {criterion}")

                # If the score is on a 0-100 scale, convert to 0-10
                if score > 10:
                    score = round(score / 10, 1)
                    logger.debug(f"Converted to 0-10 scale: {score}")

                # Map Mento-specific criteria names to standardized keys
                if "mento sdk integration" in criterion or "sdk integration" in criterion:
                    scores["mento_sdk"] = score
                    logger.debug(f"Mapped to mento_sdk: {score}")
                elif "broker contract" in criterion or "broker usage" in criterion:
                    scores["broker_contract"] = score
                    logger.debug(f"Mapped to broker_contract: {score}")
                elif "oracle implementation" in criterion or "oracle" in criterion:
                    scores["oracle_implementation"] = score
                    logger.debug(f"Mapped to oracle_implementation: {score}")
                elif "swap functionality" in criterion or "swap" in criterion:
                    scores["swap_functionality"] = score
                    logger.debug(f"Mapped to swap_functionality: {score}")
                elif "code quality" in criterion or "architecture" in criterion:
                    scores["code_quality"] = score
                    logger.debug(f"Mapped to code_quality: {score}")
                elif "overall" in criterion or "technical score" in criterion:
                    scores["overall"] = score
                    logger.debug(f"Mapped to overall: {score}")
                else:
                    logger.debug(f"Could not map criterion: {criterion}")
            except ValueError as e:
                logger.warning(f"Error parsing score '{score_str}': {e}")
                continue

    # If we couldn't find scores in a table, try individual patterns as fallback
    if not scores or len(scores) < 5:
        logger.debug(f"Falling back to individual patterns (current scores: {scores})")
        # Define patterns to look for Mento-specific scores
        patterns = {
            "mento_sdk": r"Mento\s+SDK\s+Integration\s+Quality:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "broker_contract": r"Broker\s+Contract\s+Usage:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "oracle_implementation": r"Oracle\s+Implementation:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "swap_functionality": r"Swap\s+Functionality:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "code_quality": r"Code\s+Quality\s*(?:&|and)\s*Architecture:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "overall": r"Overall\s+Technical\s+Score:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
        }

        # Extract scores using regex
        for score_name, pattern in patterns.items():
            match = re.search(pattern, markdown_content, re.IGNORECASE)
            if match:
                try:
                    # If there are multiple capture groups, find the first non-None one
                    capture_groups = match.groups()
                    score_str = next((g for g in capture_groups if g is not None), None)
                    if score_str:
                        # Remove "/10" if present in the score string
                        score_str = score_str.strip().replace("/10", "").strip()
                        score = float(score_str)
                        logger.debug(f"Found {score_name} score: {score} using pattern")

                        # If the score is on a 0-100 scale, convert to 0-10
                        if score > 10:
                            score = round(score / 10, 1)
                            logger.debug(f"Converted to 0-10 scale: {score}")

                        scores[score_name] = score
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not extract {score_name} score: {e}")

    # If we still don't have an overall score but have other scores, calculate it
    if "overall" not in scores and len(scores) >= 3:
        other_scores = [s for k, s in scores.items() if k != "overall"]
        if other_scores:
            scores["overall"] = round(sum(other_scores) / len(other_scores), 1)
            logger.debug(
                f"Calculated overall score: {scores['overall']} from {len(other_scores)} scores"
            )

    logger.debug(f"Final extracted Mento scores: {scores}")
    return scores


def extract_scores_from_markdown(markdown_content: str) -> Dict[str, float]:
    """
    Extract scores from markdown analysis content.

    Args:
        markdown_content: Markdown-formatted analysis text

    Returns:
        Dict[str, float]: Dictionary of extracted scores (0-10 scale with decimals)
    """
    scores = {}

    # For debugging
    logger.debug(f"Extracting scores from markdown content of length: {len(markdown_content)}")

    # Check for the special case where content is wrapped in ```markdown blocks
    if markdown_content.startswith("```markdown") or markdown_content.startswith("```"):
        logger.debug(
            "Content appears to be wrapped in markdown code blocks, extracting inner content"
        )
        lines = markdown_content.splitlines()
        # Find the first and last code block markers
        start_idx = next((i for i, line in enumerate(lines) if line.startswith("```")), 0)
        end_idx = (
            len(lines) - 1 - next((i for i, line in enumerate(reversed(lines)) if line == "```"), 0)
        )

        # Extract the content between the markers (if they exist)
        if start_idx < end_idx:
            # Skip the first line with ```markdown
            inner_content = "\n".join(lines[start_idx + 1 : end_idx])
            if inner_content:
                logger.debug(f"Extracted inner markdown content of length: {len(inner_content)}")
                markdown_content = inner_content

    # First try to extract from the score table (preferred method)
    # Pattern looks for a number that can be an integer or decimal followed by /10 (e.g., 8/10 or 8.5/10)
    table_pattern = r"\|\s*([^|]+)\s*\|\s*(\d+(?:\.\d+)?)(?:/10)?\s*\|"
    table_matches = re.findall(table_pattern, markdown_content)
    logger.debug(f"Found {len(table_matches)} potential score matches in table format")

    if table_matches:
        for criterion, score_str in table_matches:
            criterion = criterion.strip().lower()
            try:
                # Remove "/10" if present in the score string
                score_str = score_str.strip().replace("/10", "").strip()
                score = float(score_str)

                # Log what we found
                logger.debug(f"Found score: {score} for criterion: {criterion}")

                # If the score is on a 0-100 scale, convert to 0-10
                if score > 10:
                    score = round(score / 10, 1)
                    logger.debug(f"Converted to 0-10 scale: {score}")

                # Map various criteria names to standardized keys
                if "security" in criterion:
                    scores["security"] = score
                    logger.debug(f"Mapped to security: {score}")
                elif any(term in criterion for term in ["function", "correct"]):
                    scores["functionality"] = score
                    logger.debug(f"Mapped to functionality: {score}")
                elif any(term in criterion for term in ["read", "understand"]):
                    scores["readability"] = score
                    logger.debug(f"Mapped to readability: {score}")
                elif any(term in criterion for term in ["depend", "setup"]):
                    scores["dependencies"] = score
                    logger.debug(f"Mapped to dependencies: {score}")
                elif any(term in criterion for term in ["evidence", "technical", "usage", "celo"]):
                    scores["evidence"] = score
                    logger.debug(f"Mapped to evidence: {score}")
                elif "overall" in criterion:
                    scores["overall"] = score
                    logger.debug(f"Mapped to overall: {score}")
                else:
                    logger.debug(f"Could not map criterion: {criterion}")
            except ValueError as e:
                logger.warning(f"Error parsing score '{score_str}': {e}")
                continue

    # If we couldn't find scores in a table, try individual patterns as fallback
    if not scores or len(scores) < 5:
        logger.debug(f"Falling back to individual patterns (current scores: {scores})")
        # Define patterns to look for (allowing for decimal scores with optional /10)
        patterns = {
            "security": r"Security:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "functionality": r"Functionality\s*(?:&|and)\s*Correctness:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "readability": r"Readability:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?|Readability\s*(?:&|and)\s*Understandability:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "dependencies": r"Dependencies\s*(?:&|and)\s*Setup:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "evidence": r"Evidence\s+of\s+(?:Technical|Celo)\s+Usage:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
            "overall": r"Overall\s*(?:Score)?:?\s+(?:score)?\s*[:-]?\s*(\d+(?:\.\d+)?)(?:/10)?",
        }

        # Extract scores using regex
        for score_name, pattern in patterns.items():
            match = re.search(pattern, markdown_content, re.IGNORECASE)
            if match:
                try:
                    # If there are multiple capture groups, find the first non-None one
                    capture_groups = match.groups()
                    score_str = next((g for g in capture_groups if g is not None), None)
                    if score_str:
                        # Remove "/10" if present in the score string
                        score_str = score_str.strip().replace("/10", "").strip()
                        score = float(score_str)
                        logger.debug(f"Found {score_name} score: {score} using pattern")

                        # If the score is on a 0-100 scale, convert to 0-10
                        if score > 10:
                            score = round(score / 10, 1)
                            logger.debug(f"Converted to 0-10 scale: {score}")

                        scores[score_name] = score
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not extract {score_name} score: {e}")

    # If we still don't have an overall score but have other scores, calculate it
    if "overall" not in scores and len(scores) >= 3:
        other_scores = [s for k, s in scores.items() if k != "overall"]
        if other_scores:
            scores["overall"] = round(sum(other_scores) / len(other_scores), 1)
            logger.debug(
                f"Calculated overall score: {scores['overall']} from {len(other_scores)} scores"
            )

    logger.debug(f"Final extracted scores: {scores}")
    return scores


def update_summary_report(
    analyses: Dict[str, Union[str, Dict[str, Any]]],
    output_dir: str,
    total_repos: int,
    repos_completed: int,
) -> str:
    """
    Create or update a summary report of analyzed repositories, showing progress.

    Args:
        analyses: Dictionary mapping repository names to their analysis results
        output_dir: Directory to save the summary report
        total_repos: Total number of repositories to be analyzed
        repos_completed: Number of repositories that have been completed

    Returns:
        str: Path to the summary report file
    """
    # Ensure the output directory exists
    ensure_directory_exists(output_dir)

    # Create filename
    summary_path = os.path.join(output_dir, "summary-report.md")

    # Extract scores from each analysis
    all_scores = {}

    for repo_name, analysis in analyses.items():
        if isinstance(analysis, dict):
            # Handle JSON format
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                scores = {}
                # Extract scores from structured data
                for category in ["readability", "standards", "complexity", "testing", "overall"]:
                    if category in analysis["analysis"]:
                        score_data = analysis["analysis"][category]
                        if isinstance(score_data, dict) and "score" in score_data:
                            scores[category] = score_data["score"]
                all_scores[repo_name] = scores
        elif isinstance(analysis, str):
            # Handle markdown format
            scores = extract_scores_from_markdown(analysis)
            if scores:
                all_scores[repo_name] = scores

    # Generate markdown summary
    summary_content = "# Analysis Summary Report\n\n"
    summary_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Show progress information with visual progress bar
    progress_percentage = (repos_completed / total_repos) * 100 if total_repos > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * repos_completed // total_repos)
    progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)

    summary_content += f"## Progress: {repos_completed}/{total_repos} Repositories Analyzed ({progress_percentage:.1f}%)\n"
    summary_content += f"```\n[{progress_bar}]\n```\n\n"

    # Add status with timestamps
    summary_content += f"- Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if repos_completed == total_repos:
        summary_content += f"- Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        summary_content += (
            f"- Analysis in progress: {repos_completed} of {total_repos} repositories analyzed\n"
        )
    summary_content += "\n"

    # Add score table
    summary_content += "## Score Summary\n\n"
    summary_content += "| Repository | Security | Functionality | Readability | Dependencies | Evidence | Overall |\n"
    summary_content += "|------------|----------|--------------|-------------|--------------|----------|----------|\n"

    for repo_name, scores in all_scores.items():
        # Format scores to show on 0-10 scale with one decimal place
        security = (
            f"{scores.get('security', 'N/A')}/10" if scores.get("security") != "N/A" else "N/A"
        )
        functionality = (
            f"{scores.get('functionality', 'N/A')}/10"
            if scores.get("functionality") != "N/A"
            else "N/A"
        )
        readability = (
            f"{scores.get('readability', 'N/A')}/10"
            if scores.get("readability") != "N/A"
            else "N/A"
        )
        dependencies = (
            f"{scores.get('dependencies', 'N/A')}/10"
            if scores.get("dependencies") != "N/A"
            else "N/A"
        )
        evidence = (
            f"{scores.get('evidence', 'N/A')}/10" if scores.get("evidence") != "N/A" else "N/A"
        )
        overall = f"{scores.get('overall', 'N/A')}/10" if scores.get("overall") != "N/A" else "N/A"

        summary_content += f"| {repo_name} | {security} | {functionality} | {readability} | {dependencies} | {evidence} | {overall} |\n"

    # Add average scores if we have data
    if all_scores:
        summary_content += "\n## Average Scores\n\n"
        categories = [
            "security",
            "functionality",
            "readability",
            "dependencies",
            "evidence",
            "overall",
        ]

        for category in categories:
            scores = [
                repo_scores.get(category, 0)
                for repo_scores in all_scores.values()
                if isinstance(repo_scores.get(category, 0), (int, float))
            ]

            if scores:
                avg_score = sum(scores) / len(scores)
                summary_content += f"- **{category.title()}**: {avg_score:.1f}/10\n"

    # List completed reports
    summary_content += "\n## Individual Reports\n\n"
    for repo_name in analyses.keys():
        safe_name = repo_name.replace("/", "-")
        report_name = f"{safe_name}-analysis.md"
        summary_content += f"- [{repo_name}](./{report_name})\n"

    # Add pending repositories if not all are completed
    if repos_completed < total_repos:
        summary_content += "\n## Pending Repositories\n\n"
        summary_content += (
            f"There are {total_repos - repos_completed} repositories pending analysis.\n"
        )

    # Save summary
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)

    return summary_path


def create_summary_report(analyses: Dict[str, Union[str, Dict[str, Any]]], output_dir: str) -> str:
    """
    Create a summary report of all analyzed repositories.

    Args:
        analyses: Dictionary mapping repository names to their analysis results
        output_dir: Directory to save the summary report

    Returns:
        str: Path to the summary report file
    """
    # Call the updated function with completed = total
    return update_summary_report(analyses, output_dir, len(analyses), len(analyses))


def save_single_report(
    repo_name: str,
    analysis: Union[str, Dict[str, Any]],
    report_dir: str,
    total_repos: int,
    completed_repos: int,
    current_analyses: Dict[str, Union[str, Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Save a single repository analysis report and update the summary.

    Args:
        repo_name: Name of the repository
        analysis: Analysis result for the repository
        report_dir: Directory to save the report
        total_repos: Total number of repositories to be analyzed
        completed_repos: Number of repositories completed including this one
        current_analyses: Current collection of analyses to include in summary

    Returns:
        Dict[str, str]: Dictionary mapping repository names to their report file paths
    """
    results = {}

    # Save the individual report
    try:
        report_path = save_report(repo_name, analysis, report_dir)
        results[repo_name] = report_path

        # Update the analyses dict for the summary
        if current_analyses is None:
            current_analyses = {}
        current_analyses[repo_name] = analysis

        # Update the summary report
        try:
            summary_path = update_summary_report(
                current_analyses, report_dir, total_repos, completed_repos
            )
            results["__summary__"] = summary_path
        except Exception as e:
            logger.error(f"Error updating summary report: {str(e)}")

    except Exception as e:
        logger.error(f"Error saving report for {repo_name}: {str(e)}")

    return results


def save_reports(
    analyses: Dict[str, Union[str, Dict[str, Any]]], base_output_dir: str
) -> Dict[str, str]:
    """
    Save multiple analysis reports to files and generate summary.

    Args:
        analyses: Dictionary mapping repository names to their analysis results
        base_output_dir: Base directory for saving reports

    Returns:
        Dict[str, str]: Dictionary mapping repository names to their report file paths
    """
    results = {}

    # Create timestamped directory for this batch of reports
    report_dir = generate_report_directory(base_output_dir)

    # Save individual reports
    for repo_name, analysis in analyses.items():
        try:
            report_path = save_report(repo_name, analysis, report_dir)
            results[repo_name] = report_path
        except Exception as e:
            logger.error(f"Error saving report for {repo_name}: {str(e)}")

    # Generate summary report if we have more than one analysis
    if len(analyses) > 1:
        try:
            summary_path = create_summary_report(analyses, report_dir)
            results["__summary__"] = summary_path
        except Exception as e:
            logger.error(f"Error creating summary report: {str(e)}")

    return results


def extract_mento_features_from_markdown(markdown_content: str) -> Dict[str, Any]:
    """
    Extract Mento-specific features and implementation details from markdown analysis content.
    Focuses exclusively on Mento Protocol integration, ignoring general Celo features.

    Args:
        markdown_content: Markdown-formatted analysis text

    Returns:
        Dict[str, Any]: Dictionary containing extracted Mento features and implementation details
    """
    features = {
        "sdk_usage": [],
        "broker_integration": [],
        "oracle_usage": [],
        "stable_tokens": [],
        "advanced_features": [],
        "technical_assessment": "",
        "repo_url": ""
    }

    # Extract repository URL
    repo_url_pattern = r"(?:Repository|GitHub).*?(?:https?://)?(?:www\.)?github\.com/([^/\s]+/[^/\s]+)"
    repo_match = re.search(repo_url_pattern, markdown_content, re.IGNORECASE)
    if repo_match:
        features["repo_url"] = f"https://github.com/{repo_match.group(1)}"

    # Extract Mento SDK usage (specific to Mento, not general Celo SDK)
    sdk_patterns = [
        r"@mento-protocol/mento-sdk",
        r"mento-sdk",
        r"Mento SDK",
        r"MentoSDK",
        r"createMentoSDK",
        r"mentoSdk\.",
    ]
    for pattern in sdk_patterns:
        if re.search(pattern, markdown_content, re.IGNORECASE):
            clean_pattern = pattern.replace("r\"", "").replace("\"", "")
            features["sdk_usage"].append(clean_pattern)

    # Extract Mento broker integration details
    broker_patterns = [
        r"Broker contract",
        r"IBroker",
        r"getAmountOut",
        r"swapIn",
        r"getExchangeProviders",
        r"BiPoolManager",
        r"exchangeProvider",
        r"exchangeId",
    ]
    for pattern in broker_patterns:
        if re.search(pattern, markdown_content, re.IGNORECASE):
            clean_pattern = pattern.replace("r\"", "").replace("\"", "")
            features["broker_integration"].append(clean_pattern)

    # Extract Mento oracle usage (SortedOracles specific to Mento)
    oracle_patterns = [
        r"SortedOracles",
        r"ISortedOracles",
        r"medianRate",
        r"numRates",
        r"Oracle health",
        r"Rate feed",
        r"rateFeedId",
        r"medianTimestamp",
        r"isOldestReportExpired",
    ]
    for pattern in oracle_patterns:
        if re.search(pattern, markdown_content, re.IGNORECASE):
            clean_pattern = pattern.replace("r\"", "").replace("\"", "")
            features["oracle_usage"].append(clean_pattern)

    # Extract Mento stable token usage
    stable_token_patterns = [
        r"cUSD",
        r"cEUR", 
        r"cBRL",
        r"cXOF",
        r"cKES",
        r"cPHP",
        r"cCOP",
        r"cGHS",
        r"cGBP",
        r"cZAR",
        r"cCAD",
        r"cAUD",
        r"cCHF",
        r"cJPY",
        r"cNGN",
        r"StableToken",
        r"stable asset",
        r"mento stable",
    ]
    for pattern in stable_token_patterns:
        if re.search(pattern, markdown_content, re.IGNORECASE):
            clean_pattern = pattern.replace("r\"", "").replace("\"", "")
            features["stable_tokens"].append(clean_pattern)

    # Extract Mento advanced features
    advanced_patterns = [
        r"Multi-hop swap",
        r"Liquidity provision",
        r"Arbitrage.*mento",
        r"Circuit breaker",
        r"BreakerBox",
        r"BiPoolManager", 
        r"MedianDeltaBreaker",
        r"ValueDeltaBreaker",
        r"ConstantSum.*PricingModule",
        r"ConstantProduct.*PricingModule",
        r"Exchange.*Provider",
        r"Mento.*Reserve",
    ]
    for pattern in advanced_patterns:
        if re.search(pattern, markdown_content, re.IGNORECASE):
            clean_pattern = pattern.replace("r\"", "").replace("\"", "")
            features["advanced_features"].append(clean_pattern)

    # Extract technical assessment (Mento-specific section)
    assessment_section = re.search(
        r"## Technical Assessment.*?\n(.*?)(?=\n##|\n---|\Z)",
        markdown_content,
        re.DOTALL | re.IGNORECASE
    )
    if assessment_section:
        features["technical_assessment"] = assessment_section.group(1).strip()

    return features


def create_or_update_mento_summary(
    repo_name: str,
    analysis: Union[str, Dict[str, Any]],
    output_dir: str,
    repo_url: str = ""
) -> str:
    """
    Create or update the mento-summary.md file with project analysis.

    Args:
        repo_name: Name of the repository
        analysis: Analysis result for the repository
        output_dir: Directory where the summary file should be saved
        repo_url: GitHub URL of the repository (optional)

    Returns:
        str: Path to the mento-summary.md file
    """
    ensure_directory_exists(output_dir)
    summary_path = os.path.join(output_dir, "mento-summary.md")

    # Extract scores and features
    if isinstance(analysis, str):
        scores = extract_mento_scores_from_markdown(analysis)
        features = extract_mento_features_from_markdown(analysis)
    else:
        # Handle dict format if needed
        scores = {}
        features = {"sdk_usage": [], "broker_integration": [], "oracle_usage": [], 
                   "stable_tokens": [], "advanced_features": [], "technical_assessment": "",
                   "repo_url": repo_url}

    # Use provided repo_url or extract from analysis; ensure a valid fallback
    candidate_url = repo_url or features.get("repo_url") or f"https://github.com/{repo_name}"
    try:
        match = re.search(r"github\.com/([^/]+/[^/]+)", candidate_url, re.IGNORECASE)
        if match:
            owner_repo = match.group(1)
            if owner_repo.lower() != repo_name.lower():
                final_repo_url = f"https://github.com/{repo_name}"
            else:
                final_repo_url = candidate_url
        else:
            final_repo_url = f"https://github.com/{repo_name}"
    except Exception:
        final_repo_url = f"https://github.com/{repo_name}"

    # Create implementation summary
    implementation_parts = []
    if features["sdk_usage"]:
        implementation_parts.append("Mento SDK")
    if features["broker_integration"]:
        implementation_parts.append("Broker Contract")
    if features["oracle_usage"]:
        implementation_parts.append("Oracle Integration")
    if features["stable_tokens"]:
        implementation_parts.append("Stable Tokens")
    if features["advanced_features"]:
        implementation_parts.append("Advanced Features")

    implementation_summary = ", ".join(implementation_parts) if implementation_parts else "Basic Integration"

    # Get overall score
    overall_score = scores.get("overall")
    overall_score_display = (
        f"{overall_score}/10" if isinstance(overall_score, (int, float)) else "N/A"
    )

    # Create the project entry
    project_entry = f"""
#### Project: {repo_name}
**Repository**: [{repo_name}]({final_repo_url})  
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d')}  
**Overall Rating**: {overall_score_display}

**Key Mento Features Implemented:**
"""

    # Add feature details
    if features["sdk_usage"]:
        project_entry += f"- Mento SDK: {len(features['sdk_usage'])} features detected\n"
    if features["broker_integration"]:
        project_entry += f"- Broker Integration: {len(features['broker_integration'])} features detected\n"
    if features["oracle_usage"]:
        project_entry += f"- Oracle Usage: {len(features['oracle_usage'])} features detected\n"
    if features["stable_tokens"]:
        project_entry += f"- Stable Tokens: {len(features['stable_tokens'])} tokens/features detected\n"
    if features["advanced_features"]:
        project_entry += f"- Advanced Features: {len(features['advanced_features'])} features detected\n"

    # Add technical assessment
    if features["technical_assessment"]:
        project_entry += f"\n**Technical Assessment:**\n{features['technical_assessment'][:300]}...\n"
    else:
        project_entry += f"\n**Technical Assessment:**\nOverall score of {overall_score_display} indicates {'excellent' if isinstance(overall_score, (int, float)) and overall_score >= 8 else 'good' if isinstance(overall_score, (int, float)) and overall_score >= 6 else 'fair' if isinstance(overall_score, (int, float)) and overall_score >= 4 else 'poor' if isinstance(overall_score, (int, float)) else 'unknown'} Mento integration quality.\n"

    # Add scoring breakdown
    project_entry += f"""
**Scoring Breakdown:**
- Mento SDK Integration Quality: {scores.get('mento_sdk', 'N/A')}/10
- Broker Contract Usage: {scores.get('broker_contract', 'N/A')}/10
- Oracle Implementation: {scores.get('oracle_implementation', 'N/A')}/10
- Swap Functionality: {scores.get('swap_functionality', 'N/A')}/10
- Code Quality & Architecture: {scores.get('code_quality', 'N/A')}/10

**Recommendations:**
- [Based on analysis findings]

---
"""

    # Check if mento-summary.md already exists
    if os.path.exists(summary_path):
        # Read existing content
        with open(summary_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if this project already exists in the summary
        project_pattern = f"#### Project: {re.escape(repo_name)}"
        if re.search(project_pattern, existing_content):
            # Update existing entry
            project_section_pattern = f"(#### Project: {re.escape(repo_name)}.*?)(?=#### Project:|\\Z)"
            updated_content = re.sub(
                project_section_pattern,
                project_entry.strip(),
                existing_content,
                flags=re.DOTALL
            )
        else:
            # Add new entry
            updated_content = existing_content + project_entry

        # Update the summary table
        table_pattern = r"(\| GitHub Repository \| Mento Implementation \| Senior Developer Rating \(1-10\) \|\n\|[^\n]*\|[^\n]*\|[^\n]*\|\n)(.*?)(\n---)"
        table_match = re.search(table_pattern, updated_content, re.DOTALL)
        
        if table_match:
            # Update existing table
            table_header = table_match.group(1)
            table_footer = table_match.group(3)
            
            # Build new table row
            new_row = f"| [{repo_name}]({final_repo_url}) | {implementation_summary} | {overall_score_display} |\n"
            
            # Check if this repo already has a row
            existing_rows = table_match.group(2).strip()
            repo_row_pattern = f"\\| \\[{re.escape(repo_name)}\\].*\\n"
            
            if re.search(repo_row_pattern, existing_rows):
                # Update existing row
                updated_rows = re.sub(repo_row_pattern, new_row, existing_rows)
            else:
                # Add new row
                updated_rows = existing_rows + "\n" + new_row if existing_rows else new_row
                
            updated_content = updated_content.replace(
                table_match.group(0),
                table_header + updated_rows + table_footer
            )
    else:
        # Create new mento-summary.md file
        updated_content = f"""# Mento Protocol Integration Analysis Summary

This file contains technical assessments of projects analyzed for their Mento Protocol integration quality, rated from the perspective of a senior blockchain developer.

## Analysis Criteria

Projects are evaluated on:
- **Mento SDK Integration Quality** (0-10): Use of official SDK, proper implementation patterns
- **Broker Contract Usage** (0-10): Direct contract interactions, swap functionality
- **Oracle Implementation** (0-10): SortedOracles integration, rate handling
- **Swap Functionality** (0-10): Trading features, slippage protection, error handling
- **Code Quality & Architecture** (0-10): Overall technical implementation quality

## Project Evaluations

| GitHub Repository | Mento Implementation | Senior Developer Rating (1-10) |
|------------------|---------------------|-------------------------------|
| [{repo_name}]({final_repo_url}) | {implementation_summary} | {overall_score_display} |

---

### Individual Project Details
{project_entry}
"""

    # Save the updated content
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    logger.info(f"Updated Mento summary at: {summary_path}")
    return summary_path
