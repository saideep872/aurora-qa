# qa_engine.py
"""
Hybrid LLM-based QA engine with data sanitization.
Ensures no sensitive data (IDs, PII, financial info) goes to LLM.
Sanitization happens ONLY before sending to LLM chat completion.
"""

import requests
from openai import OpenAI
import os
from typing import List, Dict
import re
from dotenv import load_dotenv

# Loading environment variables
load_dotenv()

# Initializing OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def sanitize_message_text(text: str) -> str:
    """
    masking the sensitive information from message text.
    Only called before sending to LLM chat completion.
    """
    sanitized = text
    
    # Phone numbers 
    sanitized = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE_REDACTED]', sanitized)
    sanitized = re.sub(r'\d{3}-\d{3}-\d{4}', '[PHONE_REDACTED]', sanitized)
    sanitized = re.sub(r'\(\d{3}\)\s?\d{3}-\d{4}', '[PHONE_REDACTED]', sanitized)
    
    # Email addresses
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', sanitized)
    
    # Credit card numbers
    sanitized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]', sanitized)
    sanitized = re.sub(r'\b\d{13,19}\b', lambda m: '[CARD_REDACTED]' if len(m.group().replace('-', '').replace(' ', '')) >= 13 else m.group(), sanitized)
    
    # Social Security Numbers 
    sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', sanitized)
    
    # API keys/tokens 
    sanitized = re.sub(r'\b[A-Za-z0-9]{32,}\b', lambda m: '[TOKEN_REDACTED]' if not m.group().startswith('http') else m.group(), sanitized)
    
    # IP addresses
    sanitized = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_REDACTED]', sanitized)
    
    # Bank account numbers
    sanitized = re.sub(r'\b\d{10,}\b', lambda m: '[ACCOUNT_REDACTED]' if len(m.group()) > 9 else m.group(), sanitized)
    
    # Passwords
    sanitized = re.sub(r'(?i)\b(password|pwd|pass)[:\s]+[\w!@#$%^&*()_+-=]{6,}\b', r'\1: [PASSWORD_REDACTED]', sanitized)
    
    return sanitized


def sanitize_message(msg: Dict) -> Dict:
    """
    Sanitizing message object by:
    1. Removing sensitive fields (id, user_id)
    2. Sanitizing message text content
    3. Only including necessary fields for Q&A
    """
    return {
        "user_name": msg.get("user_name", "Unknown"),  
        "message": sanitize_message_text(msg.get("message", "")),  
        "date": msg.get("timestamp", "")[:10] if msg.get("timestamp") else None, 
    }


def get_messages():
    """Fetch all member messages from the public API."""
    url = "https://november7-730026606190.europe-west1.run.app/messages"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data.get("items", [])


def get_embedding(text: str) -> List[float]:
    """Get embedding for text. Uses original text (not sanitized)."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    return dot_product / (mag1 * mag2) if mag1 * mag2 > 0 else 0.0


def find_answer(question: str):
    
    messages = get_messages()
    
    # Step 1: Filtering by person name (optimization)
    question_lower = question.lower()
    person_matched = [
        msg for msg in messages
        if msg["user_name"].lower() in question_lower
    ]
    
  
    if person_matched:
        candidates = person_matched
        
    else:
        candidates = messages
        # For all messages, limit to reasonable size
        if len(candidates) > 100:
            candidates = candidates[:100]
    
    # Step 2: using embeddings to get top most similar messages
    question_embedding = get_embedding(question)
    scored = []
    
    for msg in candidates:
        msg_embedding = get_embedding(msg['message'])
        similarity = cosine_similarity(question_embedding, msg_embedding)
        scored.append((similarity, msg))  # Storing original message
    
    # Getting top candidates (more if person-matched for better context)
    top_count = 7 if person_matched else 10
    top_candidates = sorted(scored, key=lambda x: x[0], reverse=True)[:top_count]
    top_messages = [msg for _, msg in top_candidates]
    
    # Step 3: SANITIZING HERE - right before sending to LLM
    # Preparing sanitized messages for LLM context
    sanitized_messages = []
    for msg in top_messages:
        sanitized_msg = sanitize_message(msg)
        sanitized_messages.append(sanitized_msg)
    
    # Step 4: Formatting sanitized messages for LLM
    messages_context = "\n".join([
        f"- {msg['user_name']}: {msg['message']}" + (f" (date: {msg['date']})" if msg.get('date') else "")
        for msg in sanitized_messages
    ])
    
    # Step 5: LLM reasons about the question and generates direct answer
    system_prompt = """You are a helpful assistant that answers questions based on member messages.
Your task:
1. Read and understand the relevant messages
2. Analyze what the question is asking
3. Extract or infer the answer from the messages
4. Provide a clear, direct answer (NOT just repeating the message text)

For different question types:
- Temporal questions ("when", "what time"): Extract dates/times and answer directly
- Aggregations ("how many", "what are favorites", "list"): Analyze ALL relevant messages and summarize/aggregate
- Counting questions ("how many cars", "how many restaurants"): Count items mentioned across ALL messages
- Specific facts: Extract the exact information requested

IMPORTANT: 
- If asked "how many cars" or similar counting questions, look through ALL messages for mentions of that topic
- If asked about "favorites" or lists, aggregate all mentions from ALL messages
- If the question asks about something that might be across multiple messages, check ALL provided messages
- For counting questions, count each distinct mention (e.g., if someone mentions "3 cars", count that as 3)

Note: If you see [REDACTED] markers in messages, that indicates sensitive information that has been masked. 
Do not attempt to extract or mention the redacted information.

Answer format: Be concise and natural, as if you're directly answering the question.
Do NOT start with "According to..." or "The message says...". Just answer naturally."""
    
    user_prompt = f"""Question: "{question}"

Relevant messages:
{messages_context}

Based on these messages, answer the question directly. 
- For counting questions (like "how many cars"), count ALL mentions across ALL messages
- For aggregation questions (like "favorite restaurants"), list ALL relevant items from ALL messages
- Extract or reason about the answer from the messages
- If the information is not available in the messages, say "I couldn't find that information in the messages."

Answer:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=200
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Additional check: If LLM says "not found" but we have person-matched messages,
        # trying to return at least something relevant
        if "couldn't find" in answer.lower() and person_matched:
            
            sanitized_msg = sanitize_message(person_matched[0])
            return {
                "answer": f"Based on available information: {sanitized_msg['user_name']} mentioned: {sanitized_msg['message']}"
            }
        
        return {"answer": answer}
        
    except Exception as e:
        # Fallback: If LLM fails, return most similar message (sanitized)
        if top_messages:
            sanitized_msg = sanitize_message(top_messages[0])
            return {
                "answer": f"Based on available information: {sanitized_msg['user_name']} mentioned: {sanitized_msg['message']}"
            }
        return {"answer": "Sorry, I couldn't find a relevant answer."}


if __name__ == "__main__":
    # Testing different question types
    test_questions = [
        "When is Sophia Al-Farsi going to Paris?",
        "How many cars does Vikram Desai have?",
        "What are Amira's favorite restaurants?"
    ]
    
    for q in test_questions:
        print(f"\nQ: {q}")
        result = find_answer(q)
        print(f"A: {result['answer']}")