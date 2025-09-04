#!/usr/bin/env python3
"""
Gmail Natural Language Query Trainer
Trains AI models specifically for Gmail email management tasks
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailNLQTrainer:
    """Trainer for Gmail Natural Language Queries"""
    
    def __init__(self, base_model: str = "granite3.3-balanced"):
        self.base_model = base_model
        self.training_data = []
        self.model_name = f"{base_model}-gmail-nlq"
        
        # Gmail-specific training categories
        self.categories = {
            "email_search": "Searching and finding emails",
            "email_composition": "Composing and sending emails",
            "email_organization": "Organizing and categorizing emails",
            "email_actions": "Actions on emails (reply, forward, delete)",
            "email_analysis": "Analyzing and summarizing emails",
            "calendar_integration": "Calendar and meeting related",
            "attachment_management": "Managing email attachments",
            "spam_filtering": "Spam detection and filtering",
            "follow_up_management": "Follow-up and reminder emails",
            "template_usage": "Using email templates"
        }
    
    def generate_training_data(self) -> List[Dict[str, str]]:
        """Generate comprehensive training data for Gmail NLQ"""
        
        training_examples = []
        
        # 1. Email Search Queries
        search_queries = [
            {
                "instruction": "Do I have any new unread emails?",
                "input": "",
                "output": "I'll check your unread emails for you. Let me search for emails marked as unread in your inbox.",
                "category": "email_search",
                "intent": "read_unread_emails",
                "entities": {}
            },
            {
                "instruction": "Show me all emails marked as important",
                "input": "",
                "output": "I'll find all emails marked as important in your inbox. Let me search for emails with the IMPORTANT label.",
                "category": "email_search",
                "intent": "find_important_emails",
                "entities": {}
            },
            {
                "instruction": "List emails from John in the past week",
                "input": "",
                "output": "I'll search for emails from John sent in the past week. Let me filter by sender and date range.",
                "category": "email_search",
                "intent": "search_emails_by_sender",
                "entities": {"sender": "John", "date_range": "past week"}
            },
            {
                "instruction": "Are there any emails with attachments?",
                "input": "",
                "output": "I'll search for emails that have attachments. Let me check for emails with files, documents, or PDFs.",
                "category": "email_search",
                "intent": "find_attachments",
                "entities": {}
            },
            {
                "instruction": "Find the last email from HR",
                "input": "",
                "output": "I'll find the most recent email from HR. Let me search for emails from HR and sort by date.",
                "category": "email_search",
                "intent": "search_emails_by_sender",
                "entities": {"sender": "HR"}
            },
            {
                "instruction": "Any pending approvals in my inbox?",
                "input": "",
                "output": "I'll check for emails that need your approval or response. Let me search for pending items.",
                "category": "email_search",
                "intent": "find_pending_emails",
                "entities": {}
            },
            {
                "instruction": "Show me flagged/starred emails",
                "input": "",
                "output": "I'll show you all flagged or starred emails. Let me search for emails with the IMPORTANT label.",
                "category": "email_search",
                "intent": "find_important_emails",
                "entities": {}
            },
            {
                "instruction": "Summarize my recent emails from today",
                "input": "",
                "output": "I'll summarize all emails from today. Let me fetch today's emails and provide a summary.",
                "category": "email_search",
                "intent": "search_emails_by_date",
                "entities": {"date_range": "today"}
            }
        ]
        
        # 2. Email Composition Queries
        composition_queries = [
            {
                "instruction": "Reply to the latest email from Sarah confirming the meeting",
                "input": "",
                "output": "I'll help you reply to Sarah's latest email to confirm the meeting. Let me draft a professional response.",
                "category": "email_composition",
                "intent": "send_email",
                "entities": {"action": "reply", "sender": "Sarah", "subject": "meeting confirmation"}
            },
            {
                "instruction": "Send an email to the team about the new project timeline",
                "input": "",
                "output": "I'll help you compose an email to the team about the project timeline. Let me create a professional message.",
                "category": "email_composition",
                "intent": "send_email",
                "entities": {"recipient": "team", "subject": "project timeline"}
            },
            {
                "instruction": "Forward this email to my manager with a note",
                "input": "",
                "output": "I'll help you forward the email to your manager with an additional note. Let me prepare the forwarded message.",
                "category": "email_composition",
                "intent": "send_email",
                "entities": {"action": "forward", "recipient": "manager"}
            },
            {
                "instruction": "Draft a thank-you email for the interview",
                "input": "",
                "output": "I'll help you draft a professional thank-you email for the interview. Let me create a polite and appreciative message.",
                "category": "email_composition",
                "intent": "use_email_template",
                "entities": {"template_type": "follow_up", "context": "interview thank you"}
            },
            {
                "instruction": "Resend the last email I sent to the client",
                "input": "",
                "output": "I'll help you resend the last email to the client. Let me find the previous email and prepare it for resending.",
                "category": "email_composition",
                "intent": "send_email",
                "entities": {"action": "resend", "recipient": "client"}
            }
        ]
        
        # 3. Email Organization Queries
        organization_queries = [
            {
                "instruction": "Move all emails from GitHub to a folder named 'DevOps'",
                "input": "",
                "output": "I'll help you organize emails from GitHub into a 'DevOps' folder. Let me categorize these emails for you.",
                "category": "email_organization",
                "intent": "categorize_emails",
                "entities": {"category": "work", "folder": "DevOps", "sender": "GitHub"}
            },
            {
                "instruction": "Tag emails from recruiters as 'Job-related'",
                "input": "",
                "output": "I'll help you tag emails from recruiters as 'Job-related'. Let me categorize these emails appropriately.",
                "category": "email_organization",
                "intent": "categorize_emails",
                "entities": {"category": "personal", "tag": "Job-related", "sender": "recruiters"}
            },
            {
                "instruction": "Filter out marketing emails from my inbox",
                "input": "",
                "output": "I'll help you filter out marketing emails from your inbox. Let me identify and categorize these emails.",
                "category": "email_organization",
                "intent": "find_spam_emails",
                "entities": {"filter_type": "marketing"}
            },
            {
                "instruction": "Categorize my emails by type",
                "input": "",
                "output": "I'll categorize your emails by type (work, personal, urgent, spam, meetings). Let me organize them for you.",
                "category": "email_organization",
                "intent": "categorize_emails",
                "entities": {}
            }
        ]
        
        # 4. Email Actions Queries
        action_queries = [
            {
                "instruction": "Mark email #3 as read",
                "input": "",
                "output": "I'll mark email #3 as read for you. Let me update the email status.",
                "category": "email_actions",
                "intent": "mark_email_read",
                "entities": {"email_number": 3}
            },
            {
                "instruction": "Delete all promotional emails from my inbox",
                "input": "",
                "output": "I'll help you identify and delete promotional emails from your inbox. Let me find these emails first.",
                "category": "email_actions",
                "intent": "find_spam_emails",
                "entities": {"action": "delete", "type": "promotional"}
            },
            {
                "instruction": "Mark the latest newsletter as spam",
                "input": "",
                "output": "I'll help you mark the latest newsletter as spam. Let me identify newsletter emails for you.",
                "category": "email_actions",
                "intent": "find_spam_emails",
                "entities": {"action": "mark_spam", "type": "newsletter"}
            },
            {
                "instruction": "Archive old emails from last month",
                "input": "",
                "output": "I'll help you archive old emails from last month. Let me find emails from that time period.",
                "category": "email_actions",
                "intent": "search_emails_by_date",
                "entities": {"date_range": "last month", "action": "archive"}
            }
        ]
        
        # 5. Email Analysis Queries
        analysis_queries = [
            {
                "instruction": "Summarize all emails with project updates from this week",
                "input": "",
                "output": "I'll summarize all project update emails from this week. Let me analyze the content and provide key insights.",
                "category": "email_analysis",
                "intent": "search_emails_by_date",
                "entities": {"date_range": "this week", "content": "project updates", "action": "summarize"}
            },
            {
                "instruction": "What's the status of the invoice conversations?",
                "input": "",
                "output": "I'll analyze the invoice conversations and provide you with the current status. Let me search for invoice-related emails.",
                "category": "email_analysis",
                "intent": "search_emails",
                "entities": {"query": "invoice conversations", "action": "analyze_status"}
            },
            {
                "instruction": "Summarize this long email thread in a few bullet points",
                "input": "",
                "output": "I'll summarize this email thread into key bullet points. Let me analyze the conversation and extract the main points.",
                "category": "email_analysis",
                "intent": "summarize_email",
                "entities": {"format": "bullet points"}
            },
            {
                "instruction": "Extract action items from email #2",
                "input": "",
                "output": "I'll extract action items from email #2. Let me analyze the content and identify tasks, deadlines, and follow-ups.",
                "category": "email_analysis",
                "intent": "extract_action_items",
                "entities": {"email_number": 2}
            }
        ]
        
        # 6. Calendar Integration Queries
        calendar_queries = [
            {
                "instruction": "Schedule a meeting with Alex on Thursday at 2 PM",
                "input": "",
                "output": "I'll help you schedule a meeting with Alex on Thursday at 2 PM. Let me create a calendar event and send an invite.",
                "category": "calendar_integration",
                "intent": "create_event",
                "entities": {"attendee": "Alex", "day": "Thursday", "time": "2 PM"}
            },
            {
                "instruction": "Create a calendar invite for tomorrow's team sync",
                "input": "",
                "output": "I'll create a calendar invite for tomorrow's team sync. Let me schedule the meeting and send invitations.",
                "category": "calendar_integration",
                "intent": "create_event",
                "entities": {"event": "team sync", "day": "tomorrow"}
            },
            {
                "instruction": "Send a meeting invite based on this email content",
                "input": "",
                "output": "I'll analyze the email content and create a meeting invite based on the details mentioned. Let me extract the meeting information.",
                "category": "calendar_integration",
                "intent": "use_email_template",
                "entities": {"template_type": "meeting_confirmation", "source": "email_content"}
            }
        ]
        
        # 7. Attachment Management Queries
        attachment_queries = [
            {
                "instruction": "List emails that have PDF attachments",
                "input": "",
                "output": "I'll find all emails that have PDF attachments. Let me search for emails with PDF files.",
                "category": "attachment_management",
                "intent": "find_attachments",
                "entities": {"file_type": "PDF"}
            },
            {
                "instruction": "Find the email with the project report attached",
                "input": "",
                "output": "I'll find the email that has the project report attached. Let me search for emails with this specific attachment.",
                "category": "attachment_management",
                "intent": "find_attachments",
                "entities": {"attachment_name": "project report"}
            },
            {
                "instruction": "Send me the document attached in the last email from Ravi",
                "input": "",
                "output": "I'll help you access the document attached in Ravi's last email. Let me find the email and extract the attachment.",
                "category": "attachment_management",
                "intent": "find_attachments",
                "entities": {"sender": "Ravi", "action": "extract_attachment"}
            }
        ]
        
        # 8. Spam Filtering Queries
        spam_queries = [
            {
                "instruction": "Are there any suspicious or spam emails today?",
                "input": "",
                "output": "I'll check for suspicious or spam emails from today. Let me scan your inbox for potential spam.",
                "category": "spam_filtering",
                "intent": "find_spam_emails",
                "entities": {"date_range": "today"}
            },
            {
                "instruction": "Block all emails from this sender",
                "input": "",
                "output": "I'll help you block all emails from this sender. Let me set up the blocking rule for you.",
                "category": "spam_filtering",
                "intent": "find_spam_emails",
                "entities": {"action": "block_sender"}
            },
            {
                "instruction": "Report this email as phishing",
                "input": "",
                "output": "I'll help you report this email as phishing. Let me mark it appropriately and report it.",
                "category": "spam_filtering",
                "intent": "find_spam_emails",
                "entities": {"action": "report_phishing"}
            }
        ]
        
        # 9. Follow-up Management Queries
        followup_queries = [
            {
                "instruction": "Remind me to reply to John's email tomorrow",
                "input": "",
                "output": "I'll set a reminder for you to reply to John's email tomorrow. Let me create a calendar reminder.",
                "category": "follow_up_management",
                "intent": "generate_followup",
                "entities": {"sender": "John", "reminder_date": "tomorrow"}
            },
            {
                "instruction": "Draft a follow-up for the proposal email I sent last week",
                "input": "",
                "output": "I'll draft a follow-up email for the proposal you sent last week. Let me create a professional follow-up message.",
                "category": "follow_up_management",
                "intent": "generate_followup",
                "entities": {"context": "proposal", "date": "last week"}
            },
            {
                "instruction": "Check if the vendor replied to my quotation request",
                "input": "",
                "output": "I'll check if the vendor has replied to your quotation request. Let me search for responses from the vendor.",
                "category": "follow_up_management",
                "intent": "search_emails_by_sender",
                "entities": {"sender": "vendor", "subject": "quotation request"}
            },
            {
                "instruction": "Generate a follow-up email for email #1",
                "input": "",
                "output": "I'll generate a follow-up email for email #1. Let me create a professional follow-up based on the original email.",
                "category": "follow_up_management",
                "intent": "generate_followup",
                "entities": {"email_number": 1}
            }
        ]
        
        # 10. Template Usage Queries
        template_queries = [
            {
                "instruction": "Use the meeting confirmation template",
                "input": "",
                "output": "I'll use the meeting confirmation template for you. Let me generate a professional meeting confirmation email.",
                "category": "template_usage",
                "intent": "use_email_template",
                "entities": {"template_type": "meeting_confirmation"}
            },
            {
                "instruction": "Create a project update email using template",
                "input": "",
                "output": "I'll create a project update email using the project update template. Let me generate a structured project update.",
                "category": "template_usage",
                "intent": "use_email_template",
                "entities": {"template_type": "project_update"}
            },
            {
                "instruction": "Send a document request using template",
                "input": "",
                "output": "I'll send a document request using the document request template. Let me create a professional document request email.",
                "category": "template_usage",
                "intent": "use_email_template",
                "entities": {"template_type": "document_request"}
            }
        ]
        
        # Combine all training examples
        all_queries = (
            search_queries + composition_queries + organization_queries + 
            action_queries + analysis_queries + calendar_queries + 
            attachment_queries + spam_queries + followup_queries + template_queries
        )
        
        # Add metadata and format for training
        for query in all_queries:
            training_example = {
                "instruction": query["instruction"],
                "input": query["input"],
                "output": query["output"],
                "category": query["category"],
                "intent": query["intent"],
                "entities": query["entities"],
                "created_at": datetime.now().isoformat(),
                "model": self.model_name
            }
            training_examples.append(training_example)
        
        return training_examples
    
    def create_gmail_specialized_modelfile(self, training_examples: List[Dict[str, str]]) -> str:
        """Create a specialized modelfile for Gmail NLQ training"""
        
        # Group examples by category
        categories = {}
        for example in training_examples:
            category = example["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(example)
        
        # Create comprehensive system prompt
        system_prompt = f"""You are an expert Gmail Natural Language Query Assistant, specifically trained to understand and process email management requests.

🎯 **GMAIL NLQ SPECIALIZATION**:
- Total Training Examples: {len(training_examples)}
- Categories: {len(categories)}
- Model: {self.model_name}
- Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📧 **CORE CAPABILITIES**:
1. **Email Search & Discovery**: Find emails by sender, date, content, attachments
2. **Email Composition**: Compose, reply, forward, draft emails
3. **Email Organization**: Categorize, tag, filter, organize emails
4. **Email Actions**: Mark read/unread, delete, archive, flag emails
5. **Email Analysis**: Summarize, extract action items, analyze content
6. **Calendar Integration**: Schedule meetings, create events from emails
7. **Attachment Management**: Find, extract, manage email attachments
8. **Spam Filtering**: Detect, filter, report spam and suspicious emails
9. **Follow-up Management**: Generate follow-ups, set reminders
10. **Template Usage**: Use professional email templates

🔍 **INTENT RECOGNITION**:
- read_unread_emails: Find unread emails
- find_important_emails: Find flagged/important emails
- search_emails_by_sender: Search emails by sender
- find_attachments: Find emails with attachments
- find_pending_emails: Find emails needing attention
- send_email: Compose and send emails
- categorize_emails: Organize emails by category
- mark_email_read: Mark emails as read
- summarize_email: Summarize email content
- extract_action_items: Extract tasks and deadlines
- generate_followup: Create follow-up emails
- use_email_template: Use email templates
- create_event: Schedule calendar events
- find_spam_emails: Detect spam emails

📊 **TRAINING EXAMPLES BY CATEGORY**:"""

        # Add examples from each category
        for category, examples in categories.items():
            category_name = self.categories.get(category, category)
            system_prompt += f"\n\n### {category_name} ({len(examples)} examples):"
            
            # Add top 3 examples from each category
            for i, example in enumerate(examples[:3]):
                system_prompt += f"""

Example {i+1}:
Q: {example['instruction']}
A: {example['output']}
Intent: {example['intent']}
Entities: {example['entities']}"""
        
        system_prompt += """

🎯 **RESPONSE GUIDELINES**:
1. **Always identify the correct intent** from the user's query
2. **Extract relevant entities** (sender, date, email number, etc.)
3. **Provide clear, actionable responses** that explain what you'll do
4. **Use professional, helpful tone** for all email management tasks
5. **Suggest relevant follow-up actions** when appropriate
6. **Maintain email security and privacy** in all responses

🔒 **GMAIL BEST PRACTICES**:
- Always confirm before sending critical emails
- Respect email privacy and confidentiality
- Use appropriate email templates for common scenarios
- Provide clear explanations for email actions
- Suggest efficient email management workflows

You are now an expert Gmail NLQ assistant. Provide accurate, helpful responses for all email management queries."""

        # Create modelfile content - avoid f-string issues with curly braces
        modelfile_content = "FROM " + self.base_model + "\n\n"
        modelfile_content += 'SYSTEM """' + system_prompt + '"""\n\n'
        modelfile_content += """# Gmail NLQ specialized parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 2048
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

# Training metadata
TEMPLATE \"\"\"
{{ if .System }}{{ .System }}{{ end }}
{{ if .Prompt }}User: {{ .Prompt }}{{ end }}
Assistant: \"\"\"

PARAMETER stop "User:"
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"
"""
        
        return modelfile_content
    
    def train_model(self, training_examples: Optional[List[Dict[str, str]]] = None) -> bool:
        """Train the Gmail NLQ model"""
        
        if training_examples is None:
            training_examples = self.generate_training_data()
        
        try:
            logger.info(f"Starting Gmail NLQ model training with {len(training_examples)} examples")
            
            # Create modelfile
            modelfile_content = self.create_gmail_specialized_modelfile(training_examples)
            
            # Write modelfile to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.modelfile', delete=False) as f:
                f.write(modelfile_content)
                modelfile_path = f.name
            
            logger.info(f"Created modelfile: {modelfile_path}")
            
            # Train the model using Ollama
            result = subprocess.run([
                'ollama', 'create', self.model_name, '-f', modelfile_path
            ], capture_output=True, text=True, timeout=300)
            
            # Cleanup
            os.unlink(modelfile_path)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully trained Gmail NLQ model: {self.model_name}")
                
                # Save training data for reference
                training_data_file = f"gmail_nlq_training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(training_data_file, 'w') as f:
                    json.dump(training_examples, f, indent=2)
                
                logger.info(f"Training data saved to: {training_data_file}")
                return True
            else:
                logger.error(f"❌ Model training failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during model training: {e}")
            return False
    
    def test_model(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test the trained model with sample queries"""
        
        results = {}
        
        for query in test_queries:
            try:
                # Test using Ollama API
                result = subprocess.run([
                    'ollama', 'run', self.model_name, query
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    results[query] = {
                        "success": True,
                        "response": result.stdout.strip(),
                        "error": None
                    }
                else:
                    results[query] = {
                        "success": False,
                        "response": None,
                        "error": result.stderr.strip()
                    }
                    
            except Exception as e:
                results[query] = {
                    "success": False,
                    "response": None,
                    "error": str(e)
                }
        
        return results
    
    def generate_test_queries(self) -> List[str]:
        """Generate test queries for model validation"""
        
        test_queries = [
            "Do I have any new unread emails?",
            "Show me all emails marked as important",
            "Find emails from John in the past week",
            "Are there any emails with attachments?",
            "Reply to the latest email from Sarah",
            "Send an email to the team about the project timeline",
            "Categorize my emails by type",
            "Mark email #3 as read",
            "Summarize all project update emails from this week",
            "Schedule a meeting with Alex on Thursday at 2 PM",
            "List emails that have PDF attachments",
            "Are there any suspicious emails today?",
            "Generate a follow-up for email #1",
            "Use the meeting confirmation template"
        ]
        
        return test_queries

def main():
    """Main function to run Gmail NLQ training"""
    
    print("🚀 Gmail Natural Language Query Trainer")
    print("=" * 50)
    
    # Initialize trainer
    trainer = GmailNLQTrainer()
    
    # Generate training data
    print("📊 Generating training data...")
    training_examples = trainer.generate_training_data()
    print(f"✅ Generated {len(training_examples)} training examples")
    
    # Show training data summary
    categories = {}
    for example in training_examples:
        category = example["category"]
        categories[category] = categories.get(category, 0) + 1
    
    print("\n📈 Training Data Summary:")
    for category, count in categories.items():
        print(f"  • {trainer.categories[category]}: {count} examples")
    
    # Train the model
    print(f"\n🎯 Training Gmail NLQ model: {trainer.model_name}")
    success = trainer.train_model(training_examples)
    
    if success:
        print(f"✅ Model training completed successfully!")
        
        # Test the model
        print("\n🧪 Testing the trained model...")
        test_queries = trainer.generate_test_queries()
        results = trainer.test_model(test_queries)
        
        print("\n📋 Test Results:")
        for query, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {query}")
            if result["success"]:
                print(f"     Response: {result['response'][:100]}...")
            else:
                print(f"     Error: {result['error']}")
        
        print(f"\n🎉 Gmail NLQ model '{trainer.model_name}' is ready to use!")
        print("You can now use this model for enhanced email management capabilities.")
        
    else:
        print("❌ Model training failed. Please check the logs for details.")

if __name__ == "__main__":
    main() 