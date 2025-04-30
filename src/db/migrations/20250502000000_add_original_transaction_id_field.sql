-- migrate:up
ALTER TABLE transaction 
ADD COLUMN original_transaction_id INTEGER NULL;

ALTER TABLE transaction
ADD CONSTRAINT fk_original_transaction
  FOREIGN KEY (original_transaction_id)
  REFERENCES transaction(transaction_id)
  ON DELETE SET NULL;

-- migrate:down
ALTER TABLE transaction 
DROP CONSTRAINT IF EXISTS fk_original_transaction;

ALTER TABLE transaction 
DROP COLUMN IF EXISTS original_transaction_id;