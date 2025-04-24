-- migrate:up
ALTER TABLE category
ADD CONSTRAINT uniq_category_user_name
  UNIQUE (user_id, name);

-- migrate:down
ALTER TABLE category
DROP CONSTRAINT IF EXISTS uniq_category_user_name;