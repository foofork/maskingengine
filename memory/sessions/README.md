# Sessions Directory

This directory stores session-specific information and terminal states.

## Structure
Each session gets a unique directory:
- `session-[timestamp]/`: Session data
  - `metadata.json`: Session metadata
  - `terminal.log`: Terminal output
  - `commands.history`: Command history
  - `state.json`: Session state snapshot

## Retention Policy
Sessions are retained for 30 days by default, then archived or deleted based on configuration.

## Usage
The Claude-Flow system automatically manages session files. Do not modify these files manually.
