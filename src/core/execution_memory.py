"""
Execution Memory System.
Stores successful execution paths for faster future execution.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExecutionMemory:
    """Stores and retrieves successful execution paths."""
    
    def __init__(self, memory_file: str = "data/execution_memory.json"):
        """
        Initialize execution memory.
        
        Args:
            memory_file: Path to the memory file
        """
        self.logger = logging.getLogger(__name__)
        self.memory_file = memory_file
        self.memory = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                self.logger.info(f"Loaded {len(self.memory)} execution memories")
            else:
                self.logger.info("No existing memory file, starting fresh")
        
        except Exception as e:
            self.logger.error(f"Error loading memory: {e}")
            self.memory = {}
    
    def _save_memory(self):
        """Save memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.memory)} execution memories")
        
        except Exception as e:
            self.logger.error(f"Error saving memory: {e}")
    
    def store_execution(self, command: str, execution_path: Dict[str, Any], success: bool = True):
        """
        Store a successful execution path.
        
        Args:
            command: The command that was executed
            execution_path: Details of how the command was executed
            success: Whether the execution was successful
        """
        try:
            # Normalize command
            command_key = command.lower().strip()
            
            # Create execution record
            execution_record = {
                'command': command,
                'execution_path': execution_path,
                'success': success,
                'timestamp': datetime.now().isoformat(),
                'execution_count': 1
            }
            
            # Check if command already exists
            if command_key in self.memory:
                # Update execution count
                existing = self.memory[command_key]
                execution_record['execution_count'] = existing.get('execution_count', 0) + 1
                
                # Keep the fastest/shortest path
                existing_steps = existing.get('execution_path', {}).get('steps', [])
                new_steps = execution_path.get('steps', [])
                
                if len(new_steps) < len(existing_steps):
                    self.logger.info(f"Found shorter path for '{command}': {len(new_steps)} vs {len(existing_steps)} steps")
                    self.memory[command_key] = execution_record
                else:
                    # Just update the count
                    self.memory[command_key]['execution_count'] = execution_record['execution_count']
                    self.memory[command_key]['timestamp'] = execution_record['timestamp']
            else:
                # New command
                self.memory[command_key] = execution_record
                self.logger.info(f"Stored new execution path for '{command}'")
            
            # Save to file
            self._save_memory()
        
        except Exception as e:
            self.logger.error(f"Error storing execution: {e}")
    
    def get_execution_path(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Get the stored execution path for a command.
        
        Args:
            command: The command to look up
            
        Returns:
            Execution path if found, None otherwise
        """
        try:
            command_key = command.lower().strip()
            
            if command_key in self.memory:
                execution_record = self.memory[command_key]
                self.logger.info(f"Found stored execution path for '{command}' (used {execution_record.get('execution_count', 0)} times)")
                return execution_record.get('execution_path')
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting execution path: {e}")
            return None
    
    def has_memory(self, command: str) -> bool:
        """
        Check if there's a stored execution path for a command.
        
        Args:
            command: The command to check
            
        Returns:
            True if memory exists, False otherwise
        """
        command_key = command.lower().strip()
        return command_key in self.memory
    
    def get_all_memories(self) -> Dict[str, Any]:
        """
        Get all stored memories.
        
        Returns:
            Dictionary of all memories
        """
        return self.memory.copy()
    
    def clear_memory(self, command: Optional[str] = None):
        """
        Clear memory for a specific command or all memories.
        
        Args:
            command: Command to clear, or None to clear all
        """
        try:
            if command:
                command_key = command.lower().strip()
                if command_key in self.memory:
                    del self.memory[command_key]
                    self.logger.info(f"Cleared memory for '{command}'")
                    self._save_memory()
            else:
                self.memory = {}
                self.logger.info("Cleared all memories")
                self._save_memory()
        
        except Exception as e:
            self.logger.error(f"Error clearing memory: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories.
        
        Returns:
            Dictionary with statistics
        """
        total_commands = len(self.memory)
        total_executions = sum(m.get('execution_count', 0) for m in self.memory.values())
        
        # Most used commands
        most_used = sorted(
            self.memory.items(),
            key=lambda x: x[1].get('execution_count', 0),
            reverse=True
        )[:5]
        
        return {
            'total_commands': total_commands,
            'total_executions': total_executions,
            'most_used': [
                {
                    'command': cmd,
                    'count': data.get('execution_count', 0)
                }
                for cmd, data in most_used
            ]
        }

