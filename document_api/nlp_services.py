import os
import logging

logger = logging.getLogger(__name__)

# NLP Service Imports
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')
except ImportError:
    openai = None

try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
except (ImportError, OSError):
    spacy = None
    nlp = None

try:
    import language_tool_python
    grammar_tool = language_tool_python.LanguageTool('en-US')
except ImportError:
    language_tool_python = None
    grammar_tool = None

def check_guidelines_with_openai(text, guidelines):
    """Use OpenAI GPT to modify text according to guidelines"""
    if not openai:
        return text, ["OpenAI not available"]
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Modify the following text according to these guidelines: {guidelines}"},
                {"role": "user", "content": text}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content, []
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return text, [f"OpenAI error: {str(e)}"]

def check_guidelines_with_spacy(text, guidelines):
    """Use spaCy for text analysis and basic modifications"""
    if not nlp:
        return text, ["spaCy not available"]
    
    try:
        doc = nlp(text)
        issues = []
        
        # Basic analysis
        if "formal" in guidelines.lower():
            # Check for informal contractions
            contractions = ["don't", "won't", "can't", "isn't", "aren't"]
            for token in doc:
                if token.text.lower() in contractions:
                    issues.append(f"Informal contraction found: {token.text}")
        
        if "concise" in guidelines.lower():
            # Check sentence length
            for sent in doc.sents:
                if len(sent.text.split()) > 25:
                    issues.append(f"Long sentence detected: {sent.text[:50]}...")
        
        # Simple modifications
        modified_text = text
        if "formal" in guidelines.lower():
            modified_text = modified_text.replace("don't", "do not")
            modified_text = modified_text.replace("won't", "will not")
            modified_text = modified_text.replace("can't", "cannot")
        
        return modified_text, issues
    except Exception as e:
        logger.error(f"spaCy error: {e}")
        return text, [f"spaCy error: {str(e)}"]

def check_guidelines_with_languagetool(text, guidelines):
    """Use LanguageTool for grammar and style checking"""
    if not grammar_tool:
        return text, ["LanguageTool not available"]
    
    try:
        matches = grammar_tool.check(text)
        issues = []
        modified_text = text
        
        # Apply corrections
        for match in matches:
            if match.replacements:
                issues.append(f"Grammar issue: {match.message}")
                # Apply first suggested replacement
                modified_text = modified_text.replace(match.context, match.replacements[0])
        
        return modified_text, issues
    except Exception as e:
        logger.error(f"LanguageTool error: {e}")
        return text, [f"LanguageTool error: {str(e)}"]

def process_text_with_nlp(text, guidelines):
    """Process text using available NLP services"""
    results = {
        'original_text': text,
        'modified_text': text,
        'issues_found': [],
        'services_used': []
    }
    
    # Try OpenAI first (most comprehensive)
    if openai and os.getenv('OPENAI_API_KEY'):
        modified_text, issues = check_guidelines_with_openai(text, guidelines)
        results['modified_text'] = modified_text
        results['issues_found'].extend(issues)
        results['services_used'].append('OpenAI GPT')
        return results
    
    # Fallback to spaCy + LanguageTool
    current_text = text
    
    if nlp:
        current_text, spacy_issues = check_guidelines_with_spacy(current_text, guidelines)
        results['issues_found'].extend(spacy_issues)
        results['services_used'].append('spaCy')
    
    if grammar_tool:
        current_text, lt_issues = check_guidelines_with_languagetool(current_text, guidelines)
        results['issues_found'].extend(lt_issues)
        results['services_used'].append('LanguageTool')
    
    results['modified_text'] = current_text
    
    if not results['services_used']:
        results['issues_found'].append('No NLP services available')
        results['services_used'].append('Basic text processing')
    
    return results