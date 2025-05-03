-- migrate:up
-- Remove the user_tg_id column from user_account
ALTER TABLE user_account
DROP COLUMN IF EXISTS user_tg_id;

-- migrate:down
-- Add back the user_tg_id column with UNIQUE constraint
ALTER TABLE user_account
ADD COLUMN user_tg_id BIGINT UNIQUE NOT NULL;