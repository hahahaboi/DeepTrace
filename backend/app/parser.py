import re

# Regex to match ANSI escape sequences (color codes, text styling etc.)
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_ansi_codes(text: str) -> str:
    """
    Removes ANSI escape codes (terminal colors/formatting) from the log string.
    """
    if not text:
        return ""
    return ANSI_ESCAPE.sub('', text)

def parse_error_log(raw_log: str) -> str:
    """
    Cleans raw CI/CD logs and extracts error blocks or stack traces.
    
    Heuristics:
    1. Removes ANSI escape formatting codes.
    2. Filters out high-frequency noise (e.g., package manager progress bars, verbose debug logs).
    3. Identifies structured stack traces (Python, Node.js, Java) and captures their context.
    4. Falls back to keyword matching (error, exception, failed) if no structured traces are found.
    5. Falls back to trailing log lines if all else fails.
    """
    if not raw_log:
        return ""
        
    cleaned_log = clean_ansi_codes(raw_log)
    lines = cleaned_log.splitlines()
    
    # 1. Noise Filter Patterns
    noise_patterns = [
        re.compile(r'^\s*[\d\.\s]+[kMGT]?B\s*/\s*[\d\.\s]+[kMGT]?B\s*'), # Wget / curl / pip progress metrics
        re.compile(r'^\s*\[?[\d:\-\s\./,]+\]?\s*(?:DEBUG|INFO)\b', re.IGNORECASE), # Timestamps + Verbose debug/info tags
        re.compile(r'^[=\-\*#\s\._\+]{5,}$'), # Separator dividers
    ]
    
    filtered_lines = []
    for line in lines:
        if any(pat.match(line) for pat in noise_patterns):
            continue
        filtered_lines.append(line)
        
    # 2. Traceback & Stack Trace Extraction
    error_blocks = []
    current_block = []
    in_stack_trace = False
    
    # Specific language patterns
    traceback_start = re.compile(r'^Traceback \(most recent call last\):')
    traceback_line = re.compile(r'^\s*File\s+".*",\s*line\s+\d+.*')
    
    # General terms indicative of problems
    error_keyword = re.compile(r'(?:error|exception|failed|fatal|critical|status\s+code\s+[45]\d\d)\b', re.IGNORECASE)
    
    for i, line in enumerate(filtered_lines):
        # Python traceback
        if traceback_start.match(line):
            if current_block:
                error_blocks.append("\n".join(current_block))
                current_block = []
            in_stack_trace = True
            current_block.append(line)
            continue
            
        if in_stack_trace:
            if line.startswith(" ") or traceback_line.match(line) or "Error:" in line or "Exception:" in line:
                current_block.append(line)
                # Python tracebacks usually end with a non-indented Error/Exception statement
                if not line.startswith(" ") and ("Error:" in line or "Exception:" in line):
                    error_blocks.append("\n".join(current_block))
                    current_block = []
                    in_stack_trace = False
            else:
                if current_block:
                    error_blocks.append("\n".join(current_block))
                    current_block = []
                in_stack_trace = False
                
        # General stack trace / Java & JS formats (lines starting with 'at ...' or containing class paths)
        if not in_stack_trace:
            is_at_line = line.strip().startswith("at ") and ("(" in line or "." in line)
            if is_at_line:
                if not current_block and i > 0:
                    # Capture preceding line context if it details the exception description
                    prev = filtered_lines[i-1]
                    if error_keyword.search(prev) or "Exception" in prev:
                        current_block.append(prev)
                current_block.append(line)
            elif current_block:
                # End of current stack trace block
                error_blocks.append("\n".join(current_block))
                current_block = []
            elif error_keyword.search(line):
                # Loose lines containing explicit error terms
                error_blocks.append(line)
                
    if current_block:
        error_blocks.append("\n".join(current_block))
        
    # 3. Clean up list
    cleaned_blocks = [b.strip() for b in error_blocks if b.strip()]
    
    # 4. Fallback Strategies
    if not cleaned_blocks:
        # Fallback 1: Filter lines containing direct error terms
        fallback_lines = [line.strip() for line in filtered_lines if error_keyword.search(line)]
        if fallback_lines:
            return "\n".join(fallback_lines[:15]) # Limit to top 15 matches for brevity
        # Fallback 2: Grab the trailing lines of the log containing the failure exit
        return "\n".join([line.strip() for line in filtered_lines[-20:] if line.strip()])
        
    return "\n\n".join(cleaned_blocks)
