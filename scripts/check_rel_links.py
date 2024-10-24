#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path

class HugoLinkChecker:
    def __init__(self):
        # Patterns to check for potentially problematic URLs
        self.patterns = [
            # Direct absolute paths
            (r'(?:href|src)=[\'"]/[^\'"]*[\'"]', "Absolute path"),
            
            # Raw domains or protocols
            (r'(?:href|src)=[\'"](?:http://|https://|//)', "Hard-coded domain"),
            
            # Direct asset references without Hugo pipes
            (r'(?:href|src)=[\'"]/(?:css|js|images|img|assets)/[^\'"]*[\'"]', "Direct asset reference"),
            
            # Missing Hugo template functions
            (r'(?:href|src)=[\'"]/[^\'"]*[\'"](?!\s*\|)', "Missing Hugo URL function"),
            
            # Potentially problematic Hugo URL handling
            (r'\.Permalink(?!\s*\|)', "Raw .Permalink without processing"),
            
            # Static directory references without absURL/relURL
            (r'"/static/[^"]*"', "Static directory reference"),
        ]
        
        # File types to check
        self.file_extensions = {'.html', '.xml', '.json', '.css', '.js', '.svg'}

    def check_file(self, filepath):
        issues = []
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            line_number = 1
            for line in content.split('\n'):
                for pattern, issue_type in self.patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # Skip if it's within a Hugo template function
                        if not self.is_within_hugo_function(line, match.start()):
                            issues.append({
                                'line': line_number,
                                'content': line.strip(),
                                'match': match.group(0),
                                'type': issue_type,
                                'file': filepath
                            })
                line_number += 1
        return issues

    def is_within_hugo_function(self, line, pos):
        # Check if the match is within {{ }} template tags
        open_tags = [m.start() for m in re.finditer('{{', line[:pos])]
        close_tags = [m.start() for m in re.finditer('}}', line[:pos])]
        return len(open_tags) > len(close_tags)

    def check_directory(self, directory):
        issues = []
        for root, _, files in os.walk(directory):
            for file in files:
                if Path(file).suffix in self.file_extensions:
                    filepath = os.path.join(root, file)
                    file_issues = self.check_file(filepath)
                    issues.extend(file_issues)
        return issues

def main():
    parser = argparse.ArgumentParser(description='Check Hugo theme files for non-relative URLs')
    parser.add_argument('path', help='Path to Hugo theme directory')
    parser.add_argument('--fix', action='store_true', help='Suggest fixes for issues (not implemented yet)')
    args = parser.parse_args()

    checker = HugoLinkChecker()
    
    print(f"Checking theme files in: {args.path}")
    print("-" * 80)
    
    issues = checker.check_directory(args.path)
    
    if not issues:
        print("No issues found! 🎉")
        return

    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        if issue['file'] not in issues_by_file:
            issues_by_file[issue['file']] = []
        issues_by_file[issue['file']].append(issue)

    # Print issues organized by file
    for file, file_issues in issues_by_file.items():
        print(f"\nFile: {file}")
        print("-" * 80)
        for issue in file_issues:
            print(f"Line {issue['line']} - {issue['type']}:")
            print(f"  {issue['content']}")
            if args.fix:
                print("  Suggested fix:")
                if "href=" in issue['match']:
                    print('  Change to: href="{{ "path/to/resource" | relURL }}"')
                elif "src=" in issue['match']:
                    print('  Change to: src="{{ "path/to/resource" | relURL }}"')
                elif ".Permalink" in issue['match']:
                    print('  Change to: .RelPermalink')
            print()

    # Print summary
    print(f"\nFound {len(issues)} potential issues in {len(issues_by_file)} files.")
    print("\nCommon fixes:")
    print("1. For static assets: href={{ \"css/style.css\" | relURL }}")
    print("2. For processed assets: href={{ $style.RelPermalink }}")
    print("3. For internal links: href={{ .RelPermalink }}")
    print("4. For page references: href={{ .Site.BaseURL }}")

if __name__ == "__main__":
    main()

