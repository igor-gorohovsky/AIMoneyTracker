-- migrate:up
CREATE TABLE IF NOT EXISTS currency (
    currency_id SERIAL PRIMARY KEY,
    name        varchar(40) NOT NULL,
    iso_code    varchar(3) NOT NULL,
    symbol      varchar(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS rate (
    rate_id       SERIAL PRIMARY KEY,
    from_currency INTEGER REFERENCES currency(currency_id) ON DELETE CASCADE NOT NULL,
    to_currency   INTEGER REFERENCES currency(currency_id) ON DELETE CASCADE NOT NULL,
    rate          DECIMAL NOT NULL
);

CREATE TABLE IF NOT EXISTS user_account (
    user_id     SERIAL PRIMARY KEY,
    user_tg_id  BIGINT UNIQUE NOT NULL,
    balance     DECIMAL NOT NULL DEFAULT 0,
    currency_id INTEGER REFERENCES currency(currency_id) NOT NULL
);

CREATE TABLE IF NOT EXISTS account (
    account_id  SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES user_account(user_id) ON DELETE CASCADE NOT NULL,
    name        VARCHAR(256) NOT NULL,
    balance     DECIMAL NOT NULL,
    currency_id INTEGER REFERENCES currency(currency_id) NOT NULL
);

CREATE TABLE IF NOT EXISTS category (
    category_id SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES user_account(user_id) ON DELETE CASCADE NOT NULL,
    name        VARCHAR(256) NOT NULL,
    type        VARCHAR(256) NOT NULL
);

CREATE TABLE IF NOT EXISTS transaction (
    transaction_id SERIAL PRIMARY KEY,
    account_id     INTEGER REFERENCES account(account_id) ON DELETE CASCADE NOT NULL,
    category_id    INTEGER REFERENCES category(category_id) ON DELETE CASCADE NOT NULL,
    amount         DECIMAL NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS transaction;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS rate;
DROP TABLE IF EXISTS currency;



