-- migrate:up
ALTER TABLE transaction ADD COLUMN user_id INTEGER;
ALTER TABLE transaction ADD COLUMN withdrawal_amount DECIMAL;
ALTER TABLE transaction ADD COLUMN expense_amount DECIMAL;
ALTER TABLE transaction ADD COLUMN note TEXT;
ALTER TABLE transaction ADD COLUMN state VARCHAR(50);
ALTER TABLE transaction ADD COLUMN date TIMESTAMP WITH TIME ZONE;
ALTER TABLE transaction DROP COLUMN amount;

-- migrate:down
ALTER TABLE transaction DROP COLUMN user_id;
ALTER TABLE transaction ADD COLUMN amount DECIMAL;
ALTER TABLE transaction DROP COLUMN withdrawal_amount;
ALTER TABLE transaction DROP COLUMN expense_amount;
ALTER TABLE transaction DROP COLUMN note;
ALTER TABLE transaction DROP COLUMN state;
ALTER TABLE transaction DROP COLUMN date;
