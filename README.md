# Bank Statement Reconciliation

Quick & dirty script for bank statement reconciliation. Works with standard
statement CSVs.

## Usage

    $ python main.py < statement.csv

## CSV Format

The first row in the CSV file should be a header row, containing an entry for
each column title. Every other row represents a transaction. The columns can be
in any order, as long as they are properly labeled in the header row.

Required columns:

- Amount: transaction amount (in parenthesis if negative)

Optional columns:

- Date: date of transaction (MM/DD/YYYY)
- Description: description of transaction
- Comments: comments regarding transaction
- Check Number: check number of transaction
- Amount: amount of transaction
- Balance: Amount left after transaction

If the balance column is included, the script will verify the balance of each
row after the header row and provide the expected starting and ending balances.
Otherwise, the script will simply print the expected change in balance over all
transactions.

If no dates are provided, the script will assume that transactions are sorted
from earliest to latest. Otherwise, the script will sort the transactions by
date before processing.

You may mark transactions as pending to have the script disregard them. The
script will consider a transaction as pending if either the description
ends with the string `(Pending)` or the balance is empty.
