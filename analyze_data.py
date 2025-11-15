# analyze_data.py
"""
Comprehensive data analysis for Aurora Q&A System
Identifies anomalies, inconsistencies, and insights in member data.
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

def load_data():
    """Load messages from JSON file."""
    with open('messages_dump.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('items', [])

def analyze_temporal_patterns(messages: List[Dict]) -> Dict:
    """Analyze timestamp patterns and anomalies."""
    timestamps = []
    future_dates = []
    past_dates = []
    invalid_dates = []
    
    for msg in messages:
        ts = msg.get('timestamp')
        if not ts:
            invalid_dates.append(msg)
            continue
        
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            timestamps.append(dt)
            
            # Check for future dates (beyond reasonable range)
            if dt > datetime.now(timezone.utc):
                future_dates.append((msg['user_name'], dt, msg['message'][:50]))
            
            # Check for very old dates (before 2020)
            if dt < datetime(2020, 1, 1, tzinfo=timezone.utc):
                past_dates.append((msg['user_name'], dt, msg['message'][:50]))
        except:
            invalid_dates.append(msg)
    
    return {
        'total_messages': len(messages),
        'valid_timestamps': len(timestamps),
        'invalid_timestamps': len(invalid_dates),
        'future_dates': len(future_dates),
        'very_old_dates': len(past_dates),
        'date_range': {
            'earliest': min(timestamps).strftime("%B %d, %Y") if timestamps else None,
            'latest': max(timestamps).strftime("%B %d, %Y") if timestamps else None
        },
        'future_date_examples': future_dates[:5],
        'old_date_examples': past_dates[:5]
    }

def analyze_user_patterns(messages: List[Dict]) -> Dict:
    """Analyze user distribution and patterns."""
    user_counts = Counter(msg['user_name'] for msg in messages)
    user_ids = defaultdict(set)
    
    # Check for user_id inconsistencies
    for msg in messages:
        user_name = msg.get('user_name')
        user_id = msg.get('user_id')
        if user_name and user_id:
            user_ids[user_name].add(user_id)
    
    # Find users with multiple user_ids (inconsistency)
    inconsistent_users = {
        name: ids for name, ids in user_ids.items() 
        if len(ids) > 1
    }
    
    return {
        'total_users': len(user_counts),
        'total_messages': len(messages),
        'avg_messages_per_user': len(messages) / len(user_counts) if user_counts else 0,
        'top_10_users': dict(user_counts.most_common(10)),
        'users_with_single_message': sum(1 for count in user_counts.values() if count == 1),
        'users_with_multiple_ids': len(inconsistent_users),
        'inconsistent_user_examples': dict(list(inconsistent_users.items())[:5])
    }

def analyze_message_content(messages: List[Dict]) -> Dict:
    """Analyze message content quality and patterns."""
    empty_messages = []
    very_short = []
    very_long = []
    duplicate_messages = []
    message_texts = []
    
    # PII detection
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    card_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    
    messages_with_phone = []
    messages_with_email = []
    messages_with_card = []
    
    message_text_counter = Counter()
    
    for msg in messages:
        message = msg.get('message', '')
        message_texts.append(message)
        message_text_counter[message.lower().strip()] += 1
        
        # Length analysis
        if not message or len(message.strip()) == 0:
            empty_messages.append(msg['user_name'])
        elif len(message) < 10:
            very_short.append((msg['user_name'], message))
        elif len(message) > 500:
            very_long.append((msg['user_name'], len(message)))
        
        # PII detection
        if re.search(phone_pattern, message):
            messages_with_phone.append((msg['user_name'], message[:100]))
        if re.search(email_pattern, message):
            messages_with_email.append((msg['user_name'], message[:100]))
        if re.search(card_pattern, message):
            messages_with_card.append((msg['user_name'], message[:100]))
    
    # Find duplicates (appearing more than once)
    duplicates = {text: count for text, count in message_text_counter.items() if count > 1}
    
    return {
        'empty_messages': len(empty_messages),
        'very_short_messages': len(very_short),
        'very_long_messages': len(very_long),
        'avg_message_length': sum(len(m) for m in message_texts) / len(message_texts) if message_texts else 0,
        'duplicate_messages': len(duplicates),
        'duplicate_examples': dict(list(duplicates.items())[:5]),
        'messages_with_phone': len(messages_with_phone),
        'messages_with_email': len(messages_with_email),
        'messages_with_card': len(messages_with_card),
        'pii_examples': {
            'phone': messages_with_phone[:3],
            'email': messages_with_email[:3],
            'card': messages_with_card[:3]
        }
    }

def analyze_data_consistency(messages: List[Dict]) -> Dict:
    """Analyze data structure consistency."""
    missing_fields = {
        'id': 0,
        'user_id': 0,
        'user_name': 0,
        'timestamp': 0,
        'message': 0
    }
    
    inconsistent_names = []
    name_variations = defaultdict(set)
    
    for msg in messages:
        # Check missing fields
        for field in missing_fields:
            if not msg.get(field):
                missing_fields[field] += 1
        
        # Check name consistency (case, spacing)
        user_name = msg.get('user_name', '')
        if user_name:
            normalized = user_name.lower().strip()
            name_variations[normalized].add(user_name)
    
    # Find name variations (same person, different formatting)
    name_inconsistencies = {
        norm: list(variations) 
        for norm, variations in name_variations.items() 
        if len(variations) > 1
    }
    
    return {
        'missing_fields': missing_fields,
        'name_inconsistencies': len(name_inconsistencies),
        'name_variation_examples': dict(list(name_inconsistencies.items())[:5])
    }

def analyze_topic_distribution(messages: List[Dict]) -> Dict:
    """Analyze message topics and categories."""
    topics = {
        'travel': ['trip', 'travel', 'flight', 'jet', 'paris', 'london', 'tokyo', 'monaco', 'santorini'],
        'dining': ['restaurant', 'reservation', 'dinner', 'french laundry', 'eleven madison'],
        'entertainment': ['tickets', 'concert', 'opera', 'movie', 'premiere'],
        'accommodation': ['hotel', 'villa', 'room', 'booking'],
        'payment': ['payment', 'paid', 'processed', 'invoice', 'charge'],
        'preferences': ['prefer', 'preference', 'seat', 'aisle', 'window', 'smoking']
    }
    
    topic_counts = defaultdict(int)
    
    for msg in messages:
        message_lower = msg.get('message', '').lower()
        for topic, keywords in topics.items():
            if any(keyword in message_lower for keyword in keywords):
                topic_counts[topic] += 1
                break
    
    return {
        'topic_distribution': dict(topic_counts),
        'messages_with_no_topic_match': len(messages) - sum(topic_counts.values())
    }

def main():
    """Run comprehensive analysis."""
    print("=" * 80)
    print("AURORA Q&A SYSTEM - COMPREHENSIVE DATA ANALYSIS")
    print("=" * 80)
    
    messages = load_data()
    
    print(f"\n📊 DATASET OVERVIEW")
    print(f"Total messages: {len(messages)}")
    
    # Run all analyses
    temporal = analyze_temporal_patterns(messages)
    users = analyze_user_patterns(messages)
    content = analyze_message_content(messages)
    consistency = analyze_data_consistency(messages)
    topics = analyze_topic_distribution(messages)
    
    print("\n" + "=" * 80)
    print("TEMPORAL ANALYSIS")
    print("=" * 80)
    print(f"Valid timestamps: {temporal['valid_timestamps']}")
    print(f"Invalid timestamps: {temporal['invalid_timestamps']}")
    print(f"Future dates (anomaly): {temporal['future_dates']}")
    print(f"Very old dates (<2020): {temporal['very_old_dates']}")
    if temporal['date_range']['earliest']:
        print(f"Date range: {temporal['date_range']['earliest']} to {temporal['date_range']['latest']}")
    if temporal['future_date_examples']:
        print("\nFuture date examples:")
        for name, date, msg in temporal['future_date_examples'][:3]:
            print(f"  {name}: {date.date()} - {msg}")
    
    print("\n" + "=" * 80)
    print("USER ANALYSIS")
    print("=" * 80)
    print(f"Total unique users: {users['total_users']}")
    print(f"Average messages per user: {users['avg_messages_per_user']:.2f}")
    print(f"Users with single message: {users['users_with_single_message']}")
    print(f"Users with multiple user_ids (inconsistency): {users['users_with_multiple_ids']}")
    print("\nTop 10 users by message count:")
    for user, count in list(users['top_10_users'].items())[:10]:
        print(f"  {user}: {count} messages")
    
    print("\n" + "=" * 80)
    print("MESSAGE CONTENT ANALYSIS")
    print("=" * 80)
    print(f"Empty messages: {content['empty_messages']}")
    print(f"Very short messages (<10 chars): {content['very_short_messages']}")
    print(f"Very long messages (>500 chars): {content['very_long_messages']}")
    print(f"Average message length: {content['avg_message_length']:.1f} characters")
    print(f"Duplicate messages: {content['duplicate_messages']}")
    print(f"\nPRIVACY CONCERNS:")
    print(f"  Messages with phone numbers: {content['messages_with_phone']}")
    print(f"  Messages with email addresses: {content['messages_with_email']}")
    print(f"  Messages with credit card numbers: {content['messages_with_card']}")
    
    print("\n" + "=" * 80)
    print("DATA CONSISTENCY ANALYSIS")
    print("=" * 80)
    print("Missing fields:")
    for field, count in consistency['missing_fields'].items():
        if count > 0:
            print(f"  {field}: {count}")
    print(f"Name inconsistencies (same person, different formatting): {consistency['name_inconsistencies']}")
    
    print("\n" + "=" * 80)
    print("TOPIC DISTRIBUTION")
    print("=" * 80)
    for topic, count in sorted(topics['topic_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count} messages")
    print(f"  No topic match: {topics['messages_with_no_topic_match']} messages")
    
    print("\n" + "=" * 80)
    print("KEY FINDINGS & ANOMALIES")
    print("=" * 80)
    
    findings = []
    
    if temporal['future_dates'] > 0:
        findings.append(f"⚠️  {temporal['future_dates']} messages have future timestamps (data quality issue)")
    
    if temporal['invalid_timestamps'] > 0:
        findings.append(f"⚠️  {temporal['invalid_timestamps']} messages have invalid/missing timestamps")
    
    if users['users_with_multiple_ids'] > 0:
        findings.append(f"⚠️  {users['users_with_multiple_ids']} users have multiple user_ids (data inconsistency)")
    
    if content['messages_with_phone'] > 0:
        findings.append(f"🔒 {content['messages_with_phone']} messages contain phone numbers (privacy risk)")
    
    if content['messages_with_email'] > 0:
        findings.append(f"🔒 {content['messages_with_email']} messages contain email addresses (privacy risk)")
    
    if content['duplicate_messages'] > 0:
        findings.append(f"⚠️  {content['duplicate_messages']} duplicate messages found (data quality issue)")
    
    if consistency['name_inconsistencies'] > 0:
        findings.append(f"⚠️  {consistency['name_inconsistencies']} name formatting inconsistencies found")
    
    for finding in findings:
        print(f"  {finding}")
    
    if not findings:
        print("  ✅ No major anomalies detected")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()