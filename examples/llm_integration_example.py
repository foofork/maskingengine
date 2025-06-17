#!/usr/bin/env python
"""Example of integrating MaskingEngine with LLMs while preserving placeholders."""

import json
import openai  # Example with OpenAI, but works with any LLM
from maskingengine import Sanitizer, RehydrationPipeline, RehydrationStorage


def create_llm_prompt_with_placeholder_preservation(user_content: str) -> str:
    """
    Create a prompt that instructs the LLM to preserve placeholder tokens.
    
    This is crucial for successful rehydration!
    """
    return f"""You are a helpful assistant. Please respond to the user's request below.

IMPORTANT: The text contains placeholder tokens in the format <<TYPE_HASH_INDEX>> (like <<EMAIL_7A9B2C_1>>). 
You MUST preserve these tokens EXACTLY as they appear in your response. Do not modify, replace, or remove them.

User request: {user_content}

Remember: Keep all placeholder tokens (<<...>>) exactly as shown."""


def safe_llm_processing_example():
    """Demonstrate safe LLM processing with PII masking and rehydration."""
    
    # Setup MaskingEngine
    sanitizer = Sanitizer()
    storage = RehydrationStorage()
    pipeline = RehydrationPipeline(sanitizer, storage)
    
    # Original user input with PII
    user_input = """
    Please help me draft an email to john@example.com about the meeting. 
    I also need to mention that Sarah Johnson will be calling him at 555-123-4567.
    """
    
    print("=== Original User Input ===")
    print(user_input)
    
    # Step 1: Mask PII before sending to LLM
    session_id = "user_session_123"
    masked_content, storage_path = pipeline.sanitize_with_session(
        user_input, session_id
    )
    
    print("\\n=== Masked Content (Safe for LLM) ===")
    print(masked_content)
    
    # Step 2: Create LLM prompt with preservation instructions
    llm_prompt = create_llm_prompt_with_placeholder_preservation(masked_content)
    
    print("\\n=== LLM Prompt (with preservation instructions) ===")
    print(llm_prompt)
    
    # Step 3: Simulate LLM response (preserving placeholders)
    # In real usage, this would be: response = openai.chat.completions.create(...)
    simulated_llm_response = f"""
    I'll help you draft that email. Here's a suggested template:
    
    Subject: Meeting Discussion
    
    Dear {masked_content.split('<<')[1].split('>>')[0] if '<<' in masked_content else 'recipient'},
    
    I hope this email finds you well. I wanted to reach out regarding our upcoming meeting.
    
    Please note that <<PERSON_9E4C6A_1>> will be contacting you at <<PHONE_4D8E1F_1>> 
    to discuss the meeting details.
    
    Best regards,
    [Your name]
    
    Note: The placeholders <<EMAIL_7A9B2C_1>> and <<PHONE_4D8E1F_1>> were preserved as instructed.
    """
    
    # Fix the simulated response to use actual placeholders
    simulated_llm_response = f"""
    I'll help you draft that email. Here's a suggested template:
    
    Subject: Meeting Discussion
    
    Dear colleague,
    
    I hope this email finds you well. I wanted to reach out regarding our upcoming meeting 
    with <<EMAIL_7A9B2C_1>>.
    
    Please note that <<PERSON_9E4C6A_1>> will be contacting you at <<PHONE_4D8E1F_1>> 
    to discuss the meeting details.
    
    Best regards,
    [Your name]
    """
    
    print("\\n=== LLM Response (with preserved placeholders) ===")
    print(simulated_llm_response)
    
    # Step 4: Rehydrate the LLM response to restore original PII
    final_response = pipeline.rehydrate_with_session(
        simulated_llm_response, session_id
    )
    
    print("\\n=== Final Response (PII restored) ===")
    print(final_response)
    
    # Cleanup
    pipeline.complete_session(session_id)
    
    return final_response


def advanced_prompt_templates():
    """Examples of different prompt templates for various LLM scenarios."""
    
    templates = {
        "general_assistant": """
You are a helpful assistant. Please respond to the user's request.

CRITICAL: The text contains privacy placeholders in format <<TYPE_HASH_INDEX>>. 
You MUST keep these EXACTLY as shown. Do not change, remove, or interpret them.

User: {content}

Response (preserve all <<...>> tokens):
""",
        
        "summarization": """
Please summarize the following text. 

IMPORTANT: Keep all privacy tokens (<<TYPE_HASH_INDEX>>) unchanged in your summary.

Text to summarize: {content}

Summary (with original tokens preserved):
""",
        
        "translation": """
Translate this text to {target_language}.

CRITICAL RULE: Do NOT translate the privacy tokens <<TYPE_HASH_INDEX>>. 
Keep them exactly as they appear in the original.

Original text: {content}

Translation (keep <<...>> tokens unchanged):
""",
        
        "analysis": """
Analyze the following text for sentiment and key themes.

PRESERVE: All privacy placeholders <<TYPE_HASH_INDEX>> must remain unchanged.

Text: {content}

Analysis (maintaining original <<...>> tokens):
""",
        
        "code_generation": """
Generate code based on this description.

MANDATORY: If the description contains <<TYPE_HASH_INDEX>> tokens, 
include them exactly as placeholder values in your code.

Description: {content}

Code (preserving all <<...>> tokens as values):
""",
        
        "chat_continuation": """
Continue this conversation naturally.

RULE: Any <<TYPE_HASH_INDEX>> tokens represent private information. 
Keep them exactly as shown - do not modify or reveal what they represent.

Conversation: {content}

Response (preserve all privacy tokens):
"""
    }
    
    print("=== Advanced Prompt Templates ===")
    for use_case, template in templates.items():
        print(f"\\n**{use_case.upper().replace('_', ' ')}:**")
        print(template)


def common_mistakes_and_solutions():
    """Document common LLM integration mistakes and their solutions."""
    
    mistakes = {
        "❌ Basic prompt without preservation instruction": {
            "example": "Please summarize this text: Contact <<EMAIL_7A9B2C_1>> for details.",
            "problem": "LLM might say 'Contact the email address for details' - placeholder lost!",
            "solution": "Always include explicit placeholder preservation instructions."
        },
        
        "❌ Asking LLM to interpret placeholders": {
            "example": "What does <<EMAIL_7A9B2C_1>> represent?",
            "problem": "This defeats the purpose of masking and might confuse the LLM.",
            "solution": "Treat placeholders as opaque tokens that should pass through unchanged."
        },
        
        "❌ Using unclear placeholder formats": {
            "example": "Contact [REDACTED] for details",
            "problem": "LLM might replace [REDACTED] with actual content or modify the format.",
            "solution": "Use distinctive format like <<TYPE_HASH_INDEX>> that's clearly meant to be preserved."
        },
        
        "❌ Not validating preservation": {
            "example": "Sending LLM response directly to user without checking",
            "problem": "If placeholders were modified, rehydration will fail silently.",
            "solution": "Validate that placeholders are preserved before rehydration."
        },
        
        "❌ Complex nested instructions": {
            "example": "Rewrite this but keep the secret codes unchanged...",
            "problem": "Ambiguous instructions lead to inconsistent preservation.",
            "solution": "Use clear, explicit, simple instructions about placeholder preservation."
        }
    }
    
    print("=== Common Mistakes and Solutions ===")
    for mistake, details in mistakes.items():
        print(f"\\n{mistake}")
        print(f"Example: {details['example']}")
        print(f"Problem: {details['problem']}")
        print(f"Solution: {details['solution']}")


def validate_placeholder_preservation(original_masked: str, llm_response: str) -> bool:
    """
    Validate that the LLM preserved all placeholders correctly.
    
    Returns True if all placeholders from original are present in response.
    """
    import re
    
    # Extract placeholders from both texts
    placeholder_pattern = r'<<[A-Z0-9_]+_[A-F0-9]{6}_\d+>>'
    
    original_placeholders = set(re.findall(placeholder_pattern, original_masked))
    response_placeholders = set(re.findall(placeholder_pattern, llm_response))
    
    # Check if all original placeholders are preserved
    missing_placeholders = original_placeholders - response_placeholders
    
    if missing_placeholders:
        print(f"⚠️ Missing placeholders in LLM response: {missing_placeholders}")
        return False
    
    print("✅ All placeholders preserved correctly")
    return True


def production_integration_example():
    """Production-ready example with error handling and validation."""
    
    def safe_llm_call(masked_content: str) -> str:
        """Make LLM call with proper error handling and validation."""
        
        # Create prompt with preservation instructions
        prompt = create_llm_prompt_with_placeholder_preservation(masked_content)
        
        try:
            # Simulate LLM call (replace with your LLM client)
            # response = openai.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=0.7
            # )
            # llm_response = response.choices[0].message.content
            
            # Simulated response for demo
            llm_response = f"I'll help with that request about {masked_content}"
            
            # Validate placeholder preservation
            if not validate_placeholder_preservation(masked_content, llm_response):
                raise ValueError("LLM failed to preserve placeholders correctly")
            
            return llm_response
            
        except Exception as e:
            print(f"LLM call failed: {e}")
            # Fallback: return masked content unchanged
            return f"I received your request: {masked_content}"
    
    # Demo the production flow
    sanitizer = Sanitizer()
    storage = RehydrationStorage()
    pipeline = RehydrationPipeline(sanitizer, storage)
    
    user_input = "Please analyze the email from support@company.com about user john@example.com"
    session_id = "prod_session_456"
    
    try:
        # Mask PII
        masked_content, _ = pipeline.sanitize_with_session(user_input, session_id)
        print(f"Masked: {masked_content}")
        
        # Safe LLM processing
        llm_response = safe_llm_call(masked_content)
        print(f"LLM Response: {llm_response}")
        
        # Rehydrate
        final_response = pipeline.rehydrate_with_session(llm_response, session_id)
        print(f"Final: {final_response}")
        
    except Exception as e:
        print(f"Error in production flow: {e}")
    finally:
        # Always cleanup
        pipeline.complete_session(session_id)


if __name__ == "__main__":
    print("🔒 MaskingEngine + LLM Integration Examples\\n")
    
    print("1. Basic Integration Example")
    print("=" * 50)
    safe_llm_processing_example()
    
    print("\\n\\n2. Advanced Prompt Templates")
    print("=" * 50)
    advanced_prompt_templates()
    
    print("\\n\\n3. Common Mistakes and Solutions")
    print("=" * 50)
    common_mistakes_and_solutions()
    
    print("\\n\\n4. Production Integration")
    print("=" * 50)
    production_integration_example()
    
    print("\\n\\n🎯 Key Takeaways:")
    print("- Always include explicit placeholder preservation instructions")
    print("- Use clear, distinctive placeholder formats")
    print("- Validate placeholder preservation before rehydration")
    print("- Handle errors gracefully with fallback strategies")
    print("- Test with your specific LLM to ensure consistent behavior")