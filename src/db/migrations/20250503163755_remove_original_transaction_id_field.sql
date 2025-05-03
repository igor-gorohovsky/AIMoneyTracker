-- migrate:up
ALTER TABLE transaction DROP CONSTRAINT IF EXISTS transaction_original_transaction_id_fkey;

-- migrate:down
ALTER TABLE transaction DROP COLUMN IF EXISTS original_transaction_id;
