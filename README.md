# Aurora Q&A System

## Design Notes (Bonus 1)

### Alternative Approaches Considered

#### 1. Rule-Based Keyword Matching
- **Pros**: Fast, no external dependencies, predictable
- **Cons**: Requires hardcoded keywords, doesn't handle aggregations, fails on semantic variations
- **Why rejected**: Cannot handle questions like "favorite restaurants" or "how many cars" without extensive hardcoded rules

#### 2. Embedding-Based Semantic Search Only
- **Pros**: Semantic understanding, no hardcoded keywords, scalable
- **Cons**: Still requires post-processing for aggregations, may miss nuanced relationships
- **Why rejected**: Would need additional logic for counting/aggregating, more complex implementation

#### 3. Direct LLM Approach (Full Context)
- **Pros**: Best understanding, handles all question types
- **Cons**: Expensive (sends all messages), slower, token limits
- **Why rejected**: Cost-prohibitive for large datasets (3000+ messages)

#### 4. Hybrid Approach (Chosen) 
- **Architecture**: Embeddings filter → LLM reasons
- **Pros**: 
  - Cost-effective (only top 10-20 messages to LLM)
  - Fast (embeddings filter efficiently)
  - Accurate (LLM provides semantic understanding)
  - Handles aggregations, counting, temporal questions
- **Cons**: Requires two API calls (embeddings + chat)
- **Why chosen**: Best balance of cost, speed, and accuracy

### Implementation Details

1. **Person Name Filtering**: Pre-filters messages by person name for optimization
2. **Embedding Similarity**: Uses OpenAI embeddings to find semantically similar messages
3. **Data Sanitization**: Removes sensitive data (IDs, PII) before sending to LLM
4. **LLM Reasoning**: GPT-4o-mini reasons about top candidates and generates direct answers

AURORA Q&A SYSTEM - COMPREHENSIVE DATA ANALYSIS
================================================================================

📊 DATASET OVERVIEW
Total messages: 100

================================================================================
TEMPORAL ANALYSIS
================================================================================
Valid timestamps: 100
Invalid timestamps: 0
Future dates (anomaly): 0
Very old dates (<2020): 0
Date range: November 14, 2024 to November 04, 2025

================================================================================
USER ANALYSIS
================================================================================
Total unique users: 10
Average messages per user: 10.00
Users with single message: 0
Users with multiple user_ids (inconsistency): 0

Top 10 users by message count:
  Sophia Al-Farsi: 16 messages
  Fatima El-Tahir: 15 messages
  Hans Müller: 11 messages
  Layla Kawaguchi: 10 messages
  Vikram Desai: 10 messages
  Lily O'Sullivan: 10 messages
  Armand Dupont: 8 messages
  Thiago Monteiro: 8 messages
  Lorenzo Cavalli: 7 messages
  Amina Van Den Berg: 5 messages

================================================================================
MESSAGE CONTENT ANALYSIS
================================================================================
Empty messages: 0
Very short messages (<10 chars): 0
Very long messages (>500 chars): 0
Average message length: 63.6 characters
Duplicate messages: 0

PRIVACY CONCERNS:
  Messages with phone numbers: 7
  Messages with email addresses: 0
  Messages with credit card numbers: 0

================================================================================
DATA CONSISTENCY ANALYSIS
================================================================================
Missing fields:
Name inconsistencies (same person, different formatting): 0

================================================================================
TOPIC DISTRIBUTION
================================================================================
  travel: 17 messages
  accommodation: 11 messages
  dining: 10 messages
  entertainment: 7 messages
  preferences: 5 messages
  payment: 4 messages
  No topic match: 46 messages

================================================================================
KEY FINDINGS & ANOMALIES
================================================================================
   7 messages contain phone numbers (privacy risk)

================================================================================
