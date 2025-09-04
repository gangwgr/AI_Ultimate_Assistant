#!/usr/bin/env python3
"""
Training Script - Train models on processed documents
"""

import os
import json
import yaml
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM
)
from transformers.training_args import TrainingArguments
from transformers.trainer import Trainer
from transformers.data.data_collator import DataCollatorForLanguageModeling
from datasets import Dataset
import logging
from pathlib import Path

class DocumentTrainer:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model_name = self.config['model']['base_model']
        self.output_dir = self.config['training']['output_dir']
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_training_data(self, data_path):
        """Load training data from JSONL file"""
        examples = []
        
        with open(data_path, 'r') as f:
            for line in f:
                examples.append(json.loads(line.strip()))
        
        self.logger.info(f"Loaded {len(examples)} training examples")
        return examples
    
    def prepare_dataset(self, examples):
        """Prepare dataset for training"""
        # Format examples for training
        formatted_data = []
        
        for example in examples:
            # Create instruction-following format
            text = f"### Instruction: {example['instruction']}\n### Input: {example['input']}\n### Response: {example['output']}"
            formatted_data.append({"text": text})
        
        # Create dataset
        dataset = Dataset.from_list(formatted_data)
        
        # Tokenize
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        tokenizer.pad_token = tokenizer.eos_token
        
        def tokenize_function(examples):
            # Ensure we're working with lists
            texts = examples['text'] if isinstance(examples['text'], list) else [examples['text']]
            
            # Tokenize each text
            tokenized = tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors=None  # Return lists, not tensors
            )
            
            # Add labels for language modeling
            tokenized["labels"] = tokenized["input_ids"].copy()
            
            return tokenized
        
        tokenized_dataset = dataset.map(
            tokenize_function, 
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset, tokenizer
    
    def train_model(self, training_data_path):
        """Train the model on document data"""
        self.logger.info(f"Starting training on: {training_data_path}")
        
        # Load training data
        examples = self.load_training_data(training_data_path)
        
        # Prepare dataset
        train_dataset, tokenizer = self.prepare_dataset(examples)
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.config['training']['epochs'],
            per_device_train_batch_size=self.config['training']['batch_size'],
            gradient_accumulation_steps=self.config['training']['gradient_accumulation_steps'],
            learning_rate=self.config['training']['learning_rate'],
            logging_steps=10,
            save_steps=500,
            save_total_limit=2,
            prediction_loss_only=True,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            warmup_steps=self.config['training'].get('warmup_steps', 100),
            weight_decay=self.config['training'].get('weight_decay', 0.01),
            fp16=False,  # Disable fp16 for CPU training
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
            pad_to_multiple_of=8,
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
        
        # Train
        self.logger.info("Starting training...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        tokenizer.save_pretrained(self.output_dir)
        
        self.logger.info(f"Training complete! Model saved to: {self.output_dir}")
        
        return self.output_dir

def main():
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "training/configs/training_config.yaml"
    data_path = sys.argv[2] if len(sys.argv) > 2 else "processed/processed_training_data.jsonl"
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return
    
    if not os.path.exists(data_path):
        print(f"❌ Training data not found: {data_path}")
        return
    
    trainer = DocumentTrainer(config_path)
    model_path = trainer.train_model(data_path)
    
    print(f"\n🎉 Training complete!")
    print(f"📁 Model saved to: {model_path}")

if __name__ == "__main__":
    main()
