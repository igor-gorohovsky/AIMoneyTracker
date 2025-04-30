-- migrate:up
ALTER TABLE transaction 
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN withdrawal_amount SET NOT NULL,
    ALTER COLUMN expense_amount SET NOT NULL,
    ALTER COLUMN state SET NOT NULL,
    ALTER COLUMN date SET NOT NULL;

-- migrate:down
ALTER TABLE transaction 
    ALTER COLUMN user_id DROP NOT NULL,
    ALTER COLUMN withdrawal_amount DROP NOT NULL,
    ALTER COLUMN expense_amount DROP NOT NULL,
    ALTER COLUMN state DROP NOT NULL,
    ALTER COLUMN date DROP NOT NULL;